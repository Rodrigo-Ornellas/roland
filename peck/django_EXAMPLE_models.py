from datetime import date, timedelta
from decimal import Decimal
from django.contrib import messages
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db import transaction
from django.db.models.aggregates import Sum
from django.dispatch import receiver
from django.utils.encoding import force_unicode
from django_fsm.db.fields.fsmfield import transition, TransitionNotAllowed
from django_fsm.signals import post_transition
from rulez import registry
from rulez.rolez.models import ModelRoleMixin
from ngslims.apps.orders.managers import (SelectRelatedManager, OrderSequencingInfoManager, TubeSequencingInfoManager,
                                          SamplePrepOrderManager)
from ngslims.apps.orders.roles import Submitter, OrderManager, Technician, DataAnalysisSubmitter, DataAnalysisManager
from ngslims.apps.utils import TrackingModel, StateField
from ngslims.apps.systems.models import *
from ngslims.apps.runs import STATES as RUN_STATES
from ngslims.apps.orders import (ORDER_STATES, ANALYSIS_STATES, SAMPLE_PREP_LGTC, order_state_mask,
                                 analysis_state_mask, DEADLINE_OFFSET_DAYS)
from ngslims.apps.orders.utils import get_barcode, send_order_transition_mail, send_analysis_transition_mail
from ngslims.apps.accounts.models import User, get_automation_user


class OrderBase(TrackingModel):
    class Meta:
        abstract = True

    lgtc_order_ref = models.CharField(max_length=10, verbose_name="LGTC order reference",
                                      help_text="A reference to the LGTC order system")
    data = models.CharField(max_length=256, default="(not yet available)", blank=True)
    comment = models.TextField(default="", blank=True)
    staff_comment = models.TextField(default="", blank=True)

    @property
    def data_available(self):
        return self.data not in ('', self._meta.get_field('data').default)


class Order(OrderBase, ModelRoleMixin):
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT, verbose_name="Sequencing platform")
    experiment_type = models.ForeignKey(ExperimentType)
    indexing = models.BooleanField(default=False)
    sample_preparation = models.ForeignKey(SamplePreparationChoice)
    sample_species = models.ForeignKey(SampleSpeciesChoice)
    sample_type = models.ForeignKey(SampleTypeChoice)
    qc = models.BooleanField(default=True, verbose_name="Generate FASTQ")
    state = StateField(states=ORDER_STATES, default=ORDER_STATES.pending)
    sample_delivered = models.DateField(null=True)
    deadline = models.DateField(null=True)

    # query manager, with restriction on the depth of related objects.
    objects = SelectRelatedManager()

    class Meta:
        unique_together = ("platform", "lgtc_order_ref")

    roles = [Submitter, Technician, OrderManager]

    def __unicode__(self):
        return u" | ".join(map(lambda x: unicode(x), [self.id, self.platform, self.experiment_type,
                                                      self.created_by.last_name or self.created_by.username]))

    @property
    def state_masked(self):
        return order_state_mask(self.state)

    @property
    def status(self):
        """ Used for changelist display. This is the same as the state_masked, but with a more customer friendly name."""
        return self.state_masked.label

    @property
    def is_done(self):
        return self.state in (ORDER_STATES.succeeded, ORDER_STATES.failed)

    def _validate_indexing(self):
        if self.indexing:
            if self.sample_set.filter(index=None).count() > 0:
                raise TransitionNotAllowed('All samples should have an index.')
            if not self.mixture_set.count():
                raise TransitionNotAllowed('There should be at lease one mixture.')
            for sample in self.sample_set.filter(prep_failed=False):
                if not sample.mixture_set.count():
                    raise TransitionNotAllowed('Sample %s is not assigned to any mixture.' % sample)
            for mixture in self.mixture_set.all():
                if not mixture.tube_id.sequencinginfo_set.count():
                    raise TransitionNotAllowed('%s does not have any sequencing information' % mixture)

    @transition(field=state, source=ORDER_STATES.pending, target=ORDER_STATES.submitted,
                conditions=[lambda o, u: o.has_role(u, Submitter)],
                label='Submit', description='Submit your order for LGTC approval.')
    def submit(self, user):
        if self.sample_set.count() < 1:
            raise TransitionNotAllowed('There should be at least one sample in the order.')
        if self.sample_indexing_by_customer and self.sample_set.filter(index=None).count() > 0:
            raise TransitionNotAllowed('All samples should have an index.')
        if not self.sample_indexing_by_lgtc:
            for tube_id in self.tubeid_set.all():
                if tube_id.sequencinginfo_set.count() < 1:
                    raise TransitionNotAllowed("%s doesn't have any sequencing information." % tube_id)
        # TODO (Ticket #184): Can we generalize this to all transitions by storing who to
        #     send mail to for each transition in the permission system? Then
        #     we can attach this to a django_fsm signal.
        send_order_transition_mail(self, self.submit, User.objects.filter(is_staff=True))

    @transition(field=state, source=ORDER_STATES.submitted, target=ORDER_STATES.approved,
                conditions=[lambda o, u: o.has_role(u, OrderManager)], label='Approve')
    def approve(self, user):
        if self.dataanalysisorder_set.filter(data_analysis__require_manual_approval=True,
                                             state=ANALYSIS_STATES.pending).count() > 0:
            raise TransitionNotAllowed("Not all custom data analysis orders attached to this order are approved.")
        send_order_transition_mail(self, self.approve, [self.created_by])

    @transition(field=state, source=ORDER_STATES.submitted, target=ORDER_STATES.pending,
                conditions=[lambda o, u: o.has_role(u, OrderManager)], label='Disapprove')
    def disapprove(self, user):
        if self.comment == '':
            raise TransitionNotAllowed('Can only disapprove with a comment.')
        send_order_transition_mail(self, self.disapprove, [self.created_by])

    @transition(field=state, source=ORDER_STATES.approved, target=ORDER_STATES.delivered,
                conditions=[lambda o, u: o.has_role(u, Submitter)], label='Deliver samples',
                description="Let LGTC know that you have delivered your samples.")
    def deliver_samples(self, user):
        self.sample_delivered = date.today()
        self.deadline = date.today() + timedelta(days=DEADLINE_OFFSET_DAYS)

    @transition(field=state, source=[ORDER_STATES.delivered, ORDER_STATES.sequencing],
                target=ORDER_STATES.preparation,
                conditions=[lambda o, u: o.sample_prep_lgtc, lambda o, u: o.has_role(u, Technician)],
                label='Prepare')
    def prepare_order(self, user):
        pass

    @transition(field=state, source=[ORDER_STATES.delivered, ORDER_STATES.preparation],
                target=ORDER_STATES.sequencing, conditions=[lambda o, u: o.has_role(u, Technician)],
                label='Ready for sequencing',
                description="Mark this order as ready for sequencing so that samples are available in run designs.")
    def sequence(self, user):
        self._validate_indexing()
        if self.sample_indexing_by_lgtc:
            order_seq_info = self.sequencinginfo_set.get(tube_id__isnull=True)
            quantity_sum = self.sequencinginfo_set.filter(tube_id__isnull=False).aggregate(Sum('quantity'))
            if order_seq_info.quantity != quantity_sum['quantity__sum']:
                raise TransitionNotAllowed("The total of quantities in tube sequencing infos is not equal to the quantity defined in order sequencing info.")

    @transition(field=state, source=ORDER_STATES.sequencing, target=ORDER_STATES.succeeded,
                conditions=[lambda o, u: o.has_role(u, Technician)], label='Finish successfully')
    def success(self, user):
        for seq_info in self.sequencinginfo_set.filter(tube_id__isnull=False):
            if seq_info.quantity_left() > 0:
                raise TransitionNotAllowed("Sequencing Info %s is not done." % seq_info)
        if not self.data_available:
            raise TransitionNotAllowed('Data field should contain the link to results.')
        send_order_transition_mail(self, self.success, [self.created_by])

    @transition(field=state, source=ORDER_STATES.sequencing, target=ORDER_STATES.failed,
                conditions=[lambda o, u: o.has_role(u, Technician)],
                label='Finish in failure', description="Make sure the cause of failure is noted in the comment.")
    def fail(self, user):
        if self.comment == '':
            raise TransitionNotAllowed('Can only finish in failure with a comment.')
        if not self.data_available:
            # we will send user the data link even if it contains partial sequencing data. This failure is caused
            # by bad user sample prep, and since their sequencing fee will not be refunded, we will give them whatever
            # we have.
            raise TransitionNotAllowed('Data field should contain the link to results.')
        send_order_transition_mail(self, self.fail, [self.created_by])

    @transaction.commit_on_success
    def import_samples(self, csv_file, request=None, prep_samples=False):
        """
        Bulk import tubes and samples in a single transaction.
        Raise ValueError if one of the row cannot be imported.

        @arg csv_file:
            a csv file with header row.
        @arg request:
            the http request object that current import is happening. it's required for message logging.
        """

        import csv

        reader = csv.DictReader(csv_file, skipinitialspace=True)

        mixture_mapping = {}

        # for mixture/indexing uniqueness
        seen_data = set()

        # for bulk sample import optimization.
        barcodes = Barcode.objects.select_related(depth=1).all()

        # we cannot import SampleForm here because of circular import. Just create a generic sample form.
        from django.forms.models import modelform_factory

        SampleForm = modelform_factory(Sample, exclude=['tube_id'])

        # we don't want to log the success messages right away in case an error causing the
        # transaction to be rolled back.
        messages_success = []

        for row in reader:
            mixture_tube_id = row.get('Mixture Tube ID')
            sample_tube_id = row.get('Sample Tube ID')
            sample_id = row.get('Sample ID')

            if mixture_tube_id:
                # tube_id here is the mixture tube_id
                if mixture_tube_id in mixture_mapping:
                    mixture = mixture_mapping[mixture_tube_id]
                else:
                    try:
                        mixture = self.mixture_set.get(tube_id=mixture_tube_id, order=self)
                        mixture_mapping[mixture_tube_id] = mixture
                    except Mixture.DoesNotExist:
                        raise ValueError("Mixture %s is not found. Please first add it using the main change form. " % mixture_tube_id)
            else:
                if prep_samples:
                    raise ValueError("Row %s doesn't have a Tube ID. " % reader.line_num)
                mixture = None

            if self.indexing:
                try:
                    index = get_barcode(row.get('Index', ''), barcodes)
                except Barcode.DoesNotExist:
                    raise ValueError("Row %s has invalid index '%s'" % (reader.line_num, row.get('Index', '')))
            else:
                index = None

            if self.platform.fragment_size_required:
                try:
                    fragment_size = FragmentSizeChoice.objects.get(name=row.get('Fragment size'),
                                                                   platform=self.platform)
                except FragmentSizeChoice.DoesNotExist:
                    raise ValueError(
                        "Sample '%s' has invalid fragment size '%s'" % (sample_id, row.get('Fragment size')))
            else:
                fragment_size = None

            if mixture and index:
                pair_data = (mixture.pk, index.pk)
                if pair_data in seen_data:
                    raise ValueError("There are more than one sample with index %s in %s defined in the sample sheet."
                                     % (index, mixture.tube_id))
                seen_data.add(pair_data)

            data = {
                'name': row.get('Sample Name', sample_id),
                'concentration': row.get('Concentration (ng/ul)', Decimal('0.000')),
                'volume': row.get('Volume (ul)', 0),
                'molarity': row.get('Molarity (nM)', Decimal('0.0')),
                'index': index.pk if index else None,
                'fragment_size': fragment_size.pk if fragment_size else None,
                'order': self.pk,
                'created_by': request.user.pk,
                'modified_by': request.user.pk}

            try:
                if sample_id:
                    sample = self.sample_set.get(pk=sample_id)
                elif sample_tube_id:
                    sample = self.sample_set.get(tube_id=sample_tube_id)
                else:
                    raise Sample.DoesNotExist
                data['created_by'] = sample.created_by.pk
                action = 'updated'
            except Sample.DoesNotExist:
                # Prepare for insert.
                action = 'added'
                sample = None

            form = SampleForm(instance=sample, data=data)
            if form.is_valid():
                if form.has_changed():
                    sample = form.save()
                    sample_id = sample.pk
                    messages_success.append("Sample %s is %s." % (sample.tube_id or sample_id, action))

                if mixture:
                    # NOTE: cannot assign a sample from one tube to another.
                    if sample not in mixture.samples.all():
                        mixture.samples.add(sample)
                        messages_success.append("Sample %s is added to tube %s." % (sample_id, mixture.tube_id))
                else:
                    if not sample.tube_id:
                        sample.tube_id = TubeID.objects.create(order=self)
                        sample.save()
            else:
                raise ValueError("Sample %s has invalid value and it's not %s. Error column(s): [%s]"
                                 % (sample_id, action, ', '.join(form.errors.keys())))

        # now we know everything is fine, log the successful messages or the "No change" message.
        if not messages_success:
            messages.info(request, "No change detected.")
        else:
            for m in messages_success:
                messages.success(request, m)

    @property
    def submit_samples(self):
        return not self.platform.indexing_support or not self.indexing or self.sample_prep_lgtc

    @property
    def sample_prep_lgtc(self):
        return self.sample_preparation_id == SAMPLE_PREP_LGTC

    @property
    def sample_indexing_by_lgtc(self):
        return self.indexing and self.sample_prep_lgtc

    @property
    def sample_indexing_by_customer(self):
        return self.indexing and not self.sample_prep_lgtc

    @property
    def ready_for_prep(self):
        return self.indexing and ((self.sample_prep_lgtc and self.state > ORDER_STATES.delivered)
                                  or self.sample_indexing_by_customer)

    @property
    def tube_count(self):
        return self.mixture_set.count() if self.indexing else self.sample_set.count()

    @property
    def progress(self):
        if self.state in [ORDER_STATES.pending, ORDER_STATES.submitted, ORDER_STATES.approved]:
            return "-"
        total = 0
        done = 0
        for seq_info in self.sequencinginfo_set.filter(tube_id__isnull=False):
            total += seq_info.quantity + seq_info.repeat_quantity
            done += seq_info.finished()
        return "%d%%" % (float(done) / total * 100) if total else "-"

    def is_editable_by(self, user):
        if self.state == ORDER_STATES.pending:
            return self.has_role(user, Submitter)
        elif self.state == ORDER_STATES.submitted:
            return self.has_role(user, OrderManager)
        else:
            return self.has_role(user, Technician)

    def clean_fields(self, exclude=()):
        errors = {NON_FIELD_ERRORS: []}
        if 'platform' not in exclude:
            if self.indexing and not self.platform.indexing_support:
                errors[NON_FIELD_ERRORS].append("%s does not support indexing." % self.platform)
        if errors[NON_FIELD_ERRORS]:
            raise ValidationError(errors)

    def can_change(self, user):
        return user == self.created_by or self.has_role(user, Technician)

    def can_delete(self, user):
        return self.state == ORDER_STATES.pending and self.is_editable_by(user)

registry.register('can_change', Order)
registry.register('can_delete', Order)


@receiver(post_transition, sender=Order)
def order_post_transition(**kwargs):
    """
    receiving post transition signals for Order.

    operations defined for transition
        submit: also submit pending data analysis orders.
        success: advance approved data analysis orders to data_ready.

    :param kwargs: order instance, the name of transition, transition source, transition target.
    :return: none.
    """
    order = kwargs['instance']
    if kwargs['name'] == 'submit':
        for data_analysis_order in order.dataanalysisorder_set.filter(state=ANALYSIS_STATES.pending):
            data_analysis_order.submit(order.created_by)
            data_analysis_order.save()
    elif kwargs['name'] == 'success':
        for data_analysis_order in order.dataanalysisorder_set.filter(state=ANALYSIS_STATES.approved):
            data_analysis_order.data_ready(get_automation_user())
            data_analysis_order.save()


class SamplePrepOrder(Order):
    """
    Proxy class for Order, with filter on sample prep = LGTC and samples delivered.
    """

    class Meta:
        proxy = True

    objects = SamplePrepOrderManager()


class DataAnalysisOrder(OrderBase, ModelRoleMixin):
    data_analysis = models.ForeignKey(DataAnalysisChoice, on_delete=models.PROTECT)
    order = models.ForeignKey(Order)
    state = StateField(states=ANALYSIS_STATES, default=ANALYSIS_STATES.pending)

    roles = [DataAnalysisSubmitter, DataAnalysisManager]

    def __unicode__(self):
        return force_unicode(self.data_analysis)

    @property
    def state_masked(self):
        return analysis_state_mask(self.state)

    @transition(field=state, source=ANALYSIS_STATES.pending, target=ANALYSIS_STATES.submitted,
                conditions=[lambda o, u: o.has_role(u, DataAnalysisSubmitter)], label='Submit')
    def submit(self, user):
        send_analysis_transition_mail(self, self.submit,
                                      User.objects.filter(groups__name__in=['Bioinformatics Manager'], is_active=True))

    @transition(field=state, source=ANALYSIS_STATES.submitted, target=ANALYSIS_STATES.approved,
                conditions=[lambda o, u: o.has_role(u, DataAnalysisManager)], label='Approve')
    def approve(self, user):
        send_analysis_transition_mail(self, self.approve, [self.created_by])

    @transition(field=state, source=ANALYSIS_STATES.submitted, target=ANALYSIS_STATES.pending,
                conditions=[lambda o, u: o.has_role(u, DataAnalysisManager)], label='Disapprove')
    def disapprove(self, user):
        if self.comment == '':
            raise TransitionNotAllowed('Can only disapprove with a comment.')
        pass

    @transition(field=state, source=ANALYSIS_STATES.approved, target=ANALYSIS_STATES.ready,
                conditions=[lambda o, u: o.has_role(u, DataAnalysisManager)], label='Data ready')
    def data_ready(self, user):
        if not self.order.data_available:
            raise TransitionNotAllowed('No data from the parent sequencing order is available.')

    @transition(field=state, source=ANALYSIS_STATES.ready, target=ANALYSIS_STATES.analyzing,
                conditions=[lambda o, u: o.has_role(u, DataAnalysisManager)], label='Start analysis')
    def analyze(self, user):
        pass

    @transition(field=state, source=ANALYSIS_STATES.analyzing, target=ANALYSIS_STATES.done,
                conditions=[lambda o, u: o.has_role(u, DataAnalysisManager)], label='Finish analysis')
    def finish(self, user):
        if not self.data_available:
            raise TransitionNotAllowed('Data field should contain the link to results.')
        send_analysis_transition_mail(self, self.finish, [self.created_by])

    def can_edit(self, user):
        if self.state == ANALYSIS_STATES.pending:
            return self.has_role(user, DataAnalysisSubmitter)
        else:
            return self.has_role(user, DataAnalysisManager)

    def can_delete(self, user):
        return self.state == ANALYSIS_STATES.pending

registry.register('can_edit', DataAnalysisOrder)
registry.register('can_delete', DataAnalysisOrder)


@receiver(post_transition, sender=DataAnalysisOrder)
def dataanalysisorder_post_transition(**kwargs):
    """
    receiving post transition signals for DataAnalysisOrder.

    operations defined for transition
        submit: if the data analysis method does not require manual approval, approve it.
        approve: if its parent sequencing order is done (with data location filled in), advance to data_ready.

    :param kwargs: order instance, the name of transition, transition source, transition target.
    :return: none.
    """
    instance = kwargs['instance']

    if kwargs['name'] == 'submit':
        if not instance.data_analysis.require_manual_approval:
            instance.approve(get_automation_user())
    elif kwargs['name'] == 'approve':
        if instance.order.data_available:
            instance.data_ready(get_automation_user())


class TubeID(models.Model):
    """
    Used to track tube submission for samples or mixtures.
    Has the default auto increment id field, and that's it.
    """
    order = models.ForeignKey(Order)

    def __unicode__(self):
        return "Tube %d" % self.id

    @property
    def content(self):
        if hasattr(self, 'sample'):
            return "Sample '%s'" % self.sample
        else:
            return "Mixture with %s samples" % self.mixture.sample_count

    @property
    def progress(self):
        total = 0
        done = 0
        for seq_info in self.sequencinginfo_set.all():
            total += seq_info.quantity
            done += seq_info.finished()
        return "%d%%" % (float(done) / total * 100) if total else "-"

    @property
    def deadline(self):
        deadline = self.order.deadline
        return deadline.strftime('%d/%m/%y') if deadline else ''


class TubeRequirementsMixIn(object):

    def clean(self):
        errors = {NON_FIELD_ERRORS: []}
        try:
            requirements = self.order.platform.samplerequirement_set.get(prep_by=self.order.sample_preparation)
            for field in ['volume', 'concentration', 'molarity']:
                try:
                    value = getattr(self, field)
                    min_value = getattr(requirements, 'min_%s' % field)
                    if min_value and value and value < min_value:
                        unit = getattr(requirements, '%s_unit' % field)
                        errors[NON_FIELD_ERRORS].append("Minimum %s is %s %s. "
                                                        "Please add comment to explain why it cannot meet the minimum requirement."
                                                        % (field, min_value, unit))
                except AttributeError:
                    pass
        except SampleRequirement.DoesNotExist:
            pass

        if errors[NON_FIELD_ERRORS]:
            if self.comment:
                return errors
            else:
                # only raise error if customer doesn't provide comment for this sample
                raise ValidationError(errors)


class Sample(TubeRequirementsMixIn, TrackingModel):
    # If sample prep is done by LGTC, user will submit samples instead of tubes to an order. In this case we
    # need to link samples directly to an order.
    order = models.ForeignKey(Order)
    name = models.CharField(max_length=50, help_text="A short description of the sample")
    index = models.ForeignKey(Barcode, null=True, blank=True)
    concentration = models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True)
    volume = models.PositiveIntegerField()
    molarity = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    fragment_size = models.ForeignKey(FragmentSizeChoice, null=True, blank=True)
    tube_id = models.OneToOneField(TubeID, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)
    prep_failed = models.BooleanField(default=False)

    objects = SelectRelatedManager()

    class Meta:
        # because tube_id is an OneToOneField, tube_id will not show up in Sample model forms and thus this
        # unique_together will not be triggered automatically by django. Add it here for documentation and completeness.
        unique_together = (('tube_id', 'index'),)

    def mixture_ids(self):
        if self.pk:
            if self.mixture_set.all():
                return ", ".join([str(x.tube_id.pk) for x in self.mixture_set.all()])
            if not self.prep_failed:
                return "(Assign to mixtures)"
        return ""

    def __unicode__(self):
        return self.name


class Mixture(TubeRequirementsMixIn, TrackingModel):
    """
    A mixture can contain multiplexed samples.
    """
    order = models.ForeignKey(Order)
    samples = models.ManyToManyField(Sample)
    comment = models.CharField(max_length=255, null=True, blank=True)
    tube_id = models.OneToOneField(TubeID, null=True)

    molarity = models.DecimalField(max_digits=4, decimal_places=1)
    volume = models.PositiveIntegerField()

    @property
    def sample_count(self):
        return self.samples.count()

    def sample_ids(self):
        if not self.pk:
            return ""
        else:
            if self.samples.all():
                return ", ".join([str(x.name) for x in self.samples.all()])
            else:
                return "(Add samples)"

    def __unicode__(self):
        return "Mixture (%s)" % self.tube_id


class SequencingInfo(models.Model):
    cycles_or_time = models.ForeignKey(CyclesOrTimeChoice)
    quantity = models.IntegerField(default=1)
    tube_id = models.ForeignKey(TubeID, null=True)
    order = models.ForeignKey(Order)
    repeat_quantity = models.IntegerField(default=0, help_text='Number of times to repeat sequencing due to technical failures.')

    objects = models.Manager()
    for_orders = OrderSequencingInfoManager()
    for_tubes = TubeSequencingInfoManager()

    class Meta:
        unique_together = (('tube_id', 'cycles_or_time'),)

    def finished(self):
        return self.cell_set.exclude(run__state=RUN_STATES.failed).count()

    def quantity_left(self):
        return self.quantity + self.repeat_quantity - self.finished()

    def __unicode__(self):
        return "%s (%s)" % (self.tube_id, self.cycles_or_time)
