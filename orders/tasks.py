from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import Order


def _get_vendor_emails(order):
    return list(
        order.orderitem_set.select_related('product__vendor__user')
        .values_list('product__vendor__user__email', flat=True)
        .distinct()
    )


@shared_task
def send_order_created_email(order_id):
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return

    subject = f'Order #{order.id} created'
    buyer_message = (
        f'Hi {order.user.first_name or order.user.username},\n\n'
        f'Your order #{order.id} has been created successfully.\n'
        f'Current status: {order.status}.\n\n'
        'Thanks for shopping with us.'
    )

    if order.user.email:
        send_mail(subject, buyer_message, settings.DEFAULT_FROM_EMAIL, [order.user.email], fail_silently=True)

    vendor_emails = _get_vendor_emails(order)
    if vendor_emails:
        vendor_message = (
            f'New order #{order.id} includes one or more of your products.\n'
            f'Order status: {order.status}.'
        )
        send_mail(
            f'New vendor order #{order.id}',
            vendor_message,
            settings.DEFAULT_FROM_EMAIL,
            vendor_emails,
            fail_silently=True,
        )


@shared_task
def send_order_paid_email(order_id):
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return

    buyer_subject = f'Payment received for order #{order.id}'
    buyer_message = (
        f'Hi {order.user.first_name or order.user.username},\n\n'
        f'We received your payment for order #{order.id}.\n'
        f'Current status: {order.status}.\n\n'
        'Your order is now being processed.'
    )

    if order.user.email:
        send_mail(
            buyer_subject,
            buyer_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=True,
        )

    vendor_emails = _get_vendor_emails(order)
    if vendor_emails:
        vendor_message = (
            f'Order #{order.id} has been paid by the buyer.\n'
            'Please prepare fulfillment.'
        )
        send_mail(
            f'Paid order #{order.id}',
            vendor_message,
            settings.DEFAULT_FROM_EMAIL,
            vendor_emails,
            fail_silently=True,
        )






# # # # @shared_task
# # # # def send_test_email(receiver_email):
# # # #     subject = 'Celery Test Email'
# # # #     message = 'If you are reading this, your Celery worker and Gmail SMTP are working!'
    
# # # #     send_mail(
# # # #         subject,
# # # #         message,
# # # #         settings.DEFAULT_FROM_EMAIL,
# # # #         [receiver_email],
# # # #         fail_silently=False,
# # # #     )
# # # #     return f"Email sent to {receiver_email}"



# # # # from orders.tasks import send_test_email
# # # # task = send_test_email.delay("rizwansakhawat111@gmail.com")

# # # # print(f"Task ID: {task.id}")
# # # # print(f"Task Status: {task.status}")
