import bleach

from bakalari.models import NotificationSubscription

notification_html = """
<h3>{title}</h3>
<p>{text}</p>
</br>
</br>
<hr>
<p><a href="{login_url}">Kliknutím zde se můžete přihlásit na bakaweb.tk pro lepší přehled.</a></p>
<p>Tento email Vám byl doručen, protože jste přihlášeni k odběru novinek z Bakalářů pro uživatele {name} přes server bakaweb.tk.
Pro odhlášení klikněte <a href="{unsubscribe_url}">zde</a>.</p>
"""

notification_plain = """
{title}\n
{text}\nclient
\n
\n
----------------\n
Kliknutím zde se můžete přihlásit na bakaweb.tk pro lepší přehled:\n
{login_url}\n
\n
Tento email Vám byl doručen, protože jste přihlášeni k odběru novinek z Bakalářů pro uživatele {name} přes server bakaweb.tk.
Pro odhlášení klikněte zde:\n
{unsubscribe_url}
"""


def notification_email_data(email: str, name: str, feed_item: object, unsubscribe_url: str, average: float, login_url: str):
    def render(s):
        return s.format(
            average=str(average),
            name=name,
            title=feed_item.title,
            text=bleach.clean(feed_item.text),
            unsubscribe_url=unsubscribe_url,
            login_url=login_url
        )

    data = {
        'from': 'Bakaweb.tk <noreply@bakaweb.tk>',
        'to': email,
        'subject': '[BAKAWEB.TK] {}'.format(feed_item.title),
        'text': render(notification_plain).replace('<br>', '\n').replace('</br>','\n'),
        'html': render(notification_html)
    }
    return data


def termination_message(subscription: NotificationSubscription) -> str:
    msg = """Dobrý den,

protože se {failed_checks}x po sobě nepodařilo zkontrolovat novinky ze
školních Bakalářů pro účet "{name}", nezbývá nic jiného než Váš odběr
novinek ukončit. Pravděpodobně to je způsobeno jedním z následujících
důvodů:

1) heslo na přihlašování do Bakalářů bylo změněno
2) školní server se přesunul na jinou adresu
3) školní systém má dlouhodobě neplatný bezpečnostní certifikát
4) účet byl ze školního systému odstraněn

Pokud nenastal případ 4) a stále můžete školní systém používat, zkuste
se opětovně k notifikacím přihlásit přes web https://www.bakaweb.tk/.
Problém by tím snad měl být odstraněn. Pokud ne, tak doufám, že aspoň po
nějakou dobu Vám byla tato služba k něčemu.

Za bakaweb.tk,
Vašek Šraier"""

    return msg.format(failed_checks=subscription.failed_checks, name=subscription.name)