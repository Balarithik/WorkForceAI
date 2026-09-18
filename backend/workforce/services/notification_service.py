from django.db import IntegrityError

from workforce.models import Notification, Event


def create_notification(notification_type, title, message, severity='INFO', employee=None, task=None, event=None):
    try:
        return Notification.objects.get_or_create(
            notification_type=notification_type,
            employee=employee,
            task=task,
            event=event,
            defaults={
                'title': title,
                'message': message,
                'severity': severity,
                'is_read': False,
            },
        )[0]
    except IntegrityError:
        return Notification.objects.filter(
            notification_type=notification_type,
            employee=employee,
            task=task,
            event=event,
        ).first()


def get_notifications(unread_only=False):
    queryset = Notification.objects.select_related('employee', 'task', 'event')
    if unread_only:
        queryset = queryset.filter(is_read=False)
    return queryset.order_by('-created_at')


def mark_notification_read(notification_id):
    notification = Notification.objects.filter(id=notification_id).first()
    if notification:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    return notification


def mark_all_notifications_read():
    return Notification.objects.filter(is_read=False).update(is_read=True)


def create_event_notification(event, notification_type, title, message, severity='INFO', employee=None, task=None):
    if event is None:
        event = Event.objects.create(
            event_type='REALLOCATION',
            employee=employee,
            task=task,
            description=message,
        )
    return create_notification(
        notification_type=notification_type,
        title=title,
        message=message,
        severity=severity,
        employee=employee,
        task=task,
        event=event,
    )
