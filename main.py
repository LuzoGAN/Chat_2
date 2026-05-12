import flet as ft

# Cores do MSN 2010 Brasil
MSN_BLUE = "#0066CC"
MSN_DARK = "#003399"
MSN_LIGHT = "#E8F1FF"
MSN_GREEN = "#00B050"
MSN_GOLD = "#FFD700"
MSN_ORANGE = "#FF8C00"

# Emoticons MSN 2010
EMOTICONS = {
    ":)": "😊",
    ":(": "😢",
    ":D": "😄",
    ";)": "😉",
    ":P": "😜",
    ":/": "😕",
    ":O": "😮",
    "<3": "❤️",
    ":@": "😠",
    ":|": "😐",
}


class Message:
    def __init__(self, user_name: str, text: str, message_type: str, status: str = "online"):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type
        self.status = status

    def apply_emoticons(self, text: str) -> str:
        for emoticon, emoji in EMOTICONS.items():
            text = text.replace(emoticon, emoji)
        return text


class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.spacing = 10

        message_text = message.apply_emoticons(message.text)

        self.controls = [
            ft.CircleAvatar(
                content=ft.Text(message.user_name[:1].upper(), weight="bold", size=14),
                color=ft.colors.WHITE,
                bgcolor=self.get_avatar_color(message.user_name),
                radius=20,
            ),
            ft.Column(
                [
                    ft.Row([ft.Text(message.user_name, weight="bold", color=MSN_DARK, size=13)], spacing=5),
                    ft.Container(
                        content=ft.Text(message_text, selectable=True, size=12),
                        bgcolor=MSN_LIGHT,
                        border_radius=8,
                        padding=10,
                        border=ft.border.all(1, MSN_BLUE),
                    ),
                ],
                tight=True,
                spacing=5,
            ),
        ]

    def get_avatar_color(self, user_name: str):
        colors_lookup = [MSN_BLUE, "#9933CC", MSN_GREEN, MSN_ORANGE, "#FF6666", "#00CCFF"]
        return colors_lookup[hash(user_name) % len(colors_lookup)]


class UserItem(ft.Container):
    def __init__(self, user_name: str, status: str, is_current: bool = False):
        super().__init__()
        self.user_name = user_name
        self.status = status
        self.is_current = is_current

        status_color = MSN_GREEN if status == "online" else "#999999"

        self.content = ft.Row([
            ft.Text("●", color=status_color, size=10, weight="bold"),
            ft.Text(user_name, size=12, weight="bold" if is_current else "normal"),
        ], spacing=5)
        self.padding = 8
        self.border_radius = 5
        self.bgcolor = MSN_LIGHT if is_current else ft.colors.WHITE
        self.border = ft.border.all(1, MSN_BLUE if is_current else "#CCCCCC")


def main(page: ft.Page):
    page.title = "MSN Conversinhas - Online"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0

    logged_in_users = {}
    current_user_local = None

    # ==================== FUNÇÕES ====================

    def send_alert(user_name: str):
        page.pubsub.send_all(Message("Sistema", f"🔔 {user_name} enviou um alerta!", "alert_message"))

    def change_status(new_status: str):
        user_name = current_user_local
        if user_name:
            logged_in_users[user_name] = new_status
            update_logged_in_users()
            page.pubsub.send_all(Message("Sistema", f"{user_name} está agora {new_status}", "status_message"))

    def send_message_click(e):
        if new_message.value.strip():
            page.pubsub.send_all(Message(current_user_local, new_message.value.strip(), "chat_message"))
            new_message.value = ""
            page.update()

    def on_message(message: Message):
        if message.message_type == "chat_message":
            m = ChatMessage(message)
        elif message.message_type == "login_message":
            m = ft.Container(content=ft.Text(message.text, italic=True, color=MSN_GREEN, size=11, weight="bold"),
                             padding=5)
        elif message.message_type == "alert_message":
            m = ft.Container(content=ft.Text(message.text, italic=True, color=MSN_ORANGE, size=11), padding=5)
        elif message.message_type == "status_message":
            m = ft.Container(content=ft.Text(message.text, italic=True, color="#666666", size=10), padding=5)
        else:
            return

        chat.controls.append(m)

        if message.message_type == "login_message" and message.user_name not in logged_in_users:
            logged_in_users[message.user_name] = "online"
            update_logged_in_users()

        page.update()

    def update_logged_in_users():
        user_list.controls.clear()
        user_list.controls.append(ft.Text(f"Online ({len(logged_in_users)})", weight="bold", color=MSN_DARK, size=13))
        user_list.controls.append(ft.Divider(height=1, color=MSN_BLUE))

        for user, status in sorted(logged_in_users.items(), key=lambda x: (x[0] != current_user_local, x[0])):
            user_list.controls.append(UserItem(user, status, is_current=(user == current_user_local)))

        page.update()

    def join_chat_click(e):
        nonlocal current_user_local
        if not join_user_name.value.strip():
            join_user_name.error_text = "Por favor, digite um nome!"
            join_user_name.update()
            return

        current_user_local = join_user_name.value.strip()[:20]

        # ✅ SOLUÇÃO: Em vez de fechar dialog, troca a view inteira
        page.views.clear()
        page.views.append(main_view)

        logged_in_users[current_user_local] = "online"
        current_user_name.value = f"👤 {current_user_local}"
        new_message.prefix_text = f"{current_user_local}: "

        page.pubsub.send_all(Message("Sistema", f"➕ {current_user_local} entrou no chat!", "login_message"))
        update_logged_in_users()
        new_message.focus()
        page.update()

    def add_emoticon(emoticon: str):
        new_message.value += emoticon
        new_message.focus()
        page.update()

    # ==================== TELA DE LOGIN ====================

    join_user_name = ft.TextField(
        label="Seu Nome",
        autofocus=True,
        on_submit=join_chat_click,
        border_radius=5,
        width=300,
    )

    login_view = ft.View(
        "/login",
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Text("MSN Conversinhas", size=32, weight="bold", color=MSN_BLUE),
                    ft.Text("Bem-vindo ao chat!", size=16, color="#666"),
                    ft.Container(height=30),
                    join_user_name,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        text="Entrar no Chat",
                        on_click=join_chat_click,
                        bgcolor=MSN_GREEN,
                        color=ft.colors.WHITE,
                        width=300,
                        height=45,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True,
                bgcolor=MSN_LIGHT,
            )
        ],
        padding=0,
        bgcolor=ft.colors.WHITE,
    )

    # ==================== TELA PRINCIPAL DO CHAT ====================

    current_user_name = ft.Text("Carregando...", size=16, weight="bold", color=MSN_DARK)

    status_buttons = ft.Row([
        ft.IconButton(icon=ft.icons.CHECK_CIRCLE, tooltip="Online", on_click=lambda e: change_status("online"),
                      icon_color=MSN_GREEN),
        ft.IconButton(icon=ft.icons.BRIGHTNESS_LOW, tooltip="Ausente", on_click=lambda e: change_status("ausente"),
                      icon_color=MSN_GOLD),
        ft.IconButton(icon=ft.icons.CLOSE, tooltip="Ocupado", on_click=lambda e: change_status("ocupado"),
                      icon_color=MSN_ORANGE),
    ], spacing=0)

    alert_btn = ft.IconButton(icon=ft.icons.NOTIFICATIONS_ACTIVE, tooltip="Alerta",
                              on_click=lambda e: send_alert(current_user_local), icon_color=MSN_ORANGE)

    emoticon_buttons = ft.Row([
        ft.IconButton(icon=ft.icons.SENTIMENT_VERY_SATISFIED, tooltip=":)", on_click=lambda e: add_emoticon(" :) "),
                      icon_size=20),
        ft.IconButton(icon=ft.icons.SENTIMENT_DISSATISFIED, tooltip=":(", on_click=lambda e: add_emoticon(" :( "),
                      icon_size=20),
        ft.IconButton(icon=ft.icons.SENTIMENT_SATISFIED_ALT, tooltip=":D", on_click=lambda e: add_emoticon(" :D "),
                      icon_size=20),
        ft.IconButton(icon=ft.icons.FAVORITE, tooltip="<3", on_click=lambda e: add_emoticon(" <3 "), icon_size=20),
    ], spacing=2, scroll=ft.ScrollMode.AUTO)

    chat = ft.ListView(expand=1, spacing=8, auto_scroll=True, padding=10)
    user_list = ft.ListView(expand=1, spacing=8, auto_scroll=True, padding=10)

    new_message = ft.TextField(
        hint_text="Escreva uma mensagem...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=3,
        filled=True,
        expand=True,
        on_submit=send_message_click,
        border_radius=5,
        border_color=MSN_BLUE,
        prefix_text="",
    )

    # Layout principal
    main_layout = ft.Column([
        # Header
        ft.Container(
            content=ft.Row([ft.Text("MSN Conversinhas", size=20, weight="bold", color=ft.colors.WHITE)], expand=True),
            bgcolor=MSN_BLUE,
            padding=10,
        ),
        # User info
        ft.Container(
            content=ft.Column([
                current_user_name,
                ft.Row([ft.Text("Status:", weight="bold", size=11, color=MSN_DARK), status_buttons,
                        ft.Container(expand=True), alert_btn], spacing=5),
            ], spacing=5),
            bgcolor=MSN_LIGHT,
            padding=10,
            border=ft.border.all(1, MSN_BLUE),
        ),
        # Main area
        ft.Row([
            ft.Column([
                ft.Text("Conversa", weight="bold", color=MSN_DARK, size=12),
                ft.Container(content=chat, border=ft.border.all(1, MSN_BLUE), border_radius=5, expand=True,
                             bgcolor=ft.colors.WHITE),
            ], expand=True, spacing=5),
            ft.Column([
                ft.Text("Contatos Online", weight="bold", color=MSN_DARK, size=12),
                ft.Container(content=user_list, border=ft.border.all(1, MSN_BLUE), border_radius=5, expand=True,
                             bgcolor=ft.colors.WHITE, width=200),
            ], spacing=5),
        ], expand=True, spacing=10),
        # Emoticons
        ft.Container(content=emoticon_buttons, bgcolor=MSN_LIGHT, padding=5, border=ft.border.all(1, MSN_BLUE),
                     border_radius=5),
        # Message input
        ft.Row([new_message,
                ft.IconButton(icon=ft.icons.SEND, tooltip="Enviar", on_click=send_message_click, icon_color=MSN_BLUE)],
               spacing=5),
    ], spacing=10, expand=True)

    main_view = ft.View("/chat", controls=[main_layout], padding=10, bgcolor=ft.colors.WHITE)

    # ==================== INICIALIZAÇÃO ====================

    # ✅ SOLUÇÃO DEFINITIVA: Começa pela tela de login (view), não por dialog
    page.views.append(login_view)
    page.pubsub.subscribe(on_message)
    page.update()

    print("[MAIN] Aplicação iniciada - Tela de login exibida!")


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
