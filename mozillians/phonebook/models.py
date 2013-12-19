from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.template.loader import get_template

from funfactory.helpers import urlparams
from funfactory.urlresolvers import reverse
from funfactory.utils import absolutify
from tower import ugettext as _, ugettext_lazy as _lazy

from mozillians.users.models import UserProfile


class Invite(models.Model):
    inviter = models.ForeignKey(UserProfile, related_name='invites', null=True,
                                verbose_name=_lazy(u"Inviter"))
    recipient = models.EmailField(verbose_name=_lazy(u"Recipient"))
    message = models.TextField(blank=True, verbose_name=_lazy(u"Message"))
    redeemer = models.OneToOneField(UserProfile, blank=True, null=True,
                                    verbose_name=_lazy(u"Redeemer"))
    code = models.CharField(max_length=32, editable=False, unique=True)
    redeemed = models.DateTimeField(null=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __unicode__(self):
        return 'Invite {0} for {1}'.format(self.id, self.recipient)

    def get_url(self, absolute=True):
        """A url that can be used to redeem this invite."""
        return absolutify(
            urlparams(reverse('phonebook:register'), code=self.code))

    def send(self, sender=None):
        """Mail this invite to the specified user.

        Includes the name and email of the inviting person, if
        available.

        """
        if sender:
            sender = '%s (%s)' % (sender.full_name, sender.user.email)

        subject = _('Become a Mozillian')

        template = get_template('phonebook/invite_email.txt')

        message = template.render({
            'personal_message': self.message,
            'sender': sender or _('A fellow Mozillian'),
            'link': self.get_url()})

        # Manually replace quotes and double-quotes as these get
        # escaped by the template and this makes the message look bad.
        filtered_message = message.replace('&#34;', '"').replace('&#39;', "'")

        send_mail(subject, filtered_message, settings.FROM_NOREPLY,
                  [self.recipient])

    def send_thanks(self):
        """Sends email to person who friend accepted invitation."""
        template = get_template('phonebook/invite_accepted.txt')
        subject = _('%s created a Mozillians profile' % self.redeemer.full_name)
        profile_url = reverse('phonebook:profile_view',
                              kwargs={'username': self.redeemer.user.username})
        message = template.render({
            'inviter': self.inviter.full_name,
            'friend': self.redeemer.full_name,
            'profile': absolutify(profile_url)})
        filtered_message = message.replace('&#34;', '"').replace('&#39;', "'")

        send_mail(subject, filtered_message, settings.FROM_NOREPLY,
                  [self.inviter.email])


@receiver(models.signals.pre_save, sender=Invite)
def generate_code(sender, instance, raw, using, **kwargs):
    if instance.code or raw:
        return

    # 10 tries for uniqueness
    for i in xrange(10):
        code = get_random_string(5)
        if Invite.objects.filter(code=code).count():
            continue

    instance.code = code
