import bleach

notification_html = """
<h3>{title}</h3>
<p>{text}</p>
</br>
</br>
<hr>
<p><a href="{login_url}">Kliknutím zde si můžete zkontrolovat Vaše aktuální průměry</a></p>
<p>Tento email Vám byl doručen, protože jste přihlášeni k odběru novinek z Bakalářů pro uživatele {name} přes server bakaweb.tk.
Pro odhlášení klikňete <a href="{unsubscribe_url}">zde</a></p>.
"""

notification_plain = """
{title}\n
{text}\n
\n
\n
----------------\n
Zde si můžete zkontrolovat Vaše aktuální průměry\n
{login_url}\n
\n
Tento email Vám byl doručen, protože jste přihlášeni k odběru novinek z Bakalářů pro uživatele {name} přes server bakaweb.tk.
Pro odhlášení klikňete zde:\n
{unsubscribe_url}
"""


def notification_email_data(email: str, name: str, feed_item: object, unsubscribe_url: str, average: float, login_url: str):
    def render(s):
        return s.format(
            average=str(average),
            name=name,
            title=feed_item.title,
            text=bleach.clean(feed_item.text.replace('<br>', '\n')),
            unsubscribe_url=unsubscribe_url,
            login_url=login_url
        )

    data = {
        'from': 'Bakaweb.tk <noreply@bakaweb.tk>',
        'to': email,
        'subject': '[BAKAWEB.TK] {}'.format(feed_item.title),
        'text': render(notification_plain),
        'html': render(notification_html)
    }
    return data
