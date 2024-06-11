from .models import Messenger


def unread_messages(request):
    if request.user.is_authenticated:
        unread_messages_count = Messenger.objects.filter(receiver=request.user, is_read=False).count()
        return {'unread_messages': unread_messages_count}
    return {}
