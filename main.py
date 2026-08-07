import flet as ft
import base64

# 🎨 Cores clássicas do MSN Messenger (Brasil)
MSN_BLUE = "#0054A6"
MSN_BLUE_DARK = "#003366"
MSN_BLUE_LIGHT = "#CCE5FF"
MSN_GREEN = "#4FBA6F"
MSN_GOLD = "#FFB900"
MSN_RED = "#E81123"
MSN_WHITE = "#FFFFFF"
MSN_GRAY = "#F0F0F0"
MSN_BORDER = "#99C9EF"

# 😄 Emoticons clássicos do MSN
EMOTICONS = {
    ":)": "😊", ":(": "😢", ":D": "😄", ";)": "😉",
    ":P": "😜", ":/": "😕", ":O": "😮", "<3": "❤️",
    ":@": "😠", ":|": "😐", "8)": "😎", "(Y)": "👍",
    "(N)": "👎", ":$": "😳", "(H)": "😎",
}


class Message:
    def __init__(self, user_name: str, text: str, message_type: str,
                 status: str = "online", image_data: str = None,
                 original_user: str = None, is_nudge: bool = False):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type
        self.status = status
        self.image_data = image_data
        self.original_user = original_user
        self.is_nudge = is_nudge

    def apply_emoticons(self, text: str) -> str:
        for emoticon, emoji in EMOTICONS.items():
            text = text.replace(emoticon, emoji)
        return text


class MSNMessageBubble(ft.Row):
    """Balão de mensagem estilo MSN clássico"""

    def __init__(self, message: Message, page_ref: ft.Page, current_user: str):
        super().__init__()
        self._page_ref = page_ref
        self.message = message
        self.current_user = current_user
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.spacing = 8

        text = message.apply_emoticons(message.text) if message.text else ""
        is_mine = message.user_name == current_user

        bubble_color = MSN_BLUE_LIGHT if not is_mine else "#E8F5E9"
        border_color = MSN_BLUE if not is_mine else MSN_GREEN

        bubble_content = [
            ft.Text(
                f"{message.user_name} diz:" if not is_mine else "Você diz:",
                weight="bold",
                size=11,
                color=MSN_BLUE_DARK,
            ),
        ]

        if message.image_data:
            # ✅ CORREÇÃO: Usa src com data URI em vez de src_base64
            img_src = f"data:image/png;base64,{message.image_data}"
            img = ft.Image(
                src=img_src,
                width=220,
                height=180,
                fit="cover",
                border_radius=6,
            )
            bubble_content.append(
                ft.Container(
                    content=img,
                    on_click=lambda e: self._show_full_image(message.image_data),
                    ink=True,
                    border_radius=6,
                    tooltip="Clique para ampliar 🖼️",
                )
            )

        if text:
            bubble_content.append(
                ft.Text(text, selectable=True, size=13, color="#000000")
            )

        bubble = ft.Container(
            content=ft.Column(bubble_content, spacing=4, tight=True),
            bgcolor=bubble_color,
            border_radius=10,
            padding=10,
            border=ft.Border.all(1, border_color),
        )

        avatar_color = self._get_avatar_color(message.user_name)
        avatar = ft.CircleAvatar(
            content=ft.Text(message.user_name[:1].upper(), weight="bold", size=13, color=MSN_WHITE),
            bgcolor=avatar_color,
            radius=18,
        )

        if is_mine:
            self.controls = [ft.Container(expand=True), avatar, bubble]
        else:
            self.controls = [avatar, bubble]

    def _get_avatar_color(self, user_name: str):
        colors = ["#0066CC", "#9933CC", "#00B050", "#FF8C00", "#E81123", "#00CCFF", "#FF6666"]
        return colors[hash(user_name) % len(colors)]

    def _show_full_image(self, image_data):
        def close_dlg(e):
            dlg.open = False
            self._page_ref.update()

        # ✅ CORREÇÃO: Usa src com data URI
        img_src = f"data:image/png;base64,{image_data}"
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.IMAGE, color=MSN_BLUE),
                ft.Text("Imagem em tamanho completo", weight="bold"),
            ]),
            content=ft.Container(
                content=ft.Image(
                    src=img_src,
                    width=650,
                    height=550,
                    fit="contain",
                ),
                padding=10,
            ),
            actions=[ft.TextButton("Fechar", on_click=close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page_ref.overlay.append(dlg)
        dlg.open = True
        self._page_ref.update()


class UserListItem(ft.Container):
    """Item da lista de contatos online estilo MSN"""

    def __init__(self, user_name: str, status: str, is_current: bool = False):
        super().__init__()
        self.user_name = user_name
        self.status = status
        self.is_current_user = is_current

        status_map = {
            "online": (MSN_GREEN, "Online"),
            "ausente": (MSN_GOLD, "Ausente"),
            "ocupado": (MSN_RED, "Ocupado"),
        }
        color, label = status_map.get(status, ("#999999", "Offline"))

        self.content = ft.Row([
            ft.Icon(ft.Icons.PERSON, size=16, color=MSN_BLUE_DARK),
            ft.Text(user_name, size=12, weight="bold" if is_current else "normal",
                    color=MSN_BLUE_DARK, expand=True),
            ft.Container(
                content=ft.Text("●", color=color, size=10, weight="bold"),
                tooltip=label,
            ),
        ], spacing=6)
        self.padding = 8
        self.border_radius = 4
        self.bgcolor = MSN_BLUE_LIGHT if is_current else MSN_WHITE
        self.ink = True


def main(page: ft.Page):
    page.title = "MSN Conversinhas - Messenger Clássico"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.window.width = 1000
    page.window.height = 700
    page.window.min_width = 800
    page.window.min_height = 600

    logged_in_users = {}
    current_user_local = None

    # ==================== FUNÇÕES PRINCIPAIS ====================

    def send_nudge(user_name: str):
        page.pubsub.send_all(Message(
            "Sistema",
            f"📢 {user_name} te chamou atenção!",
            "nudge_message",
            original_user=user_name,
            is_nudge=True
        ))

    def send_alert(user_name: str):
        page.pubsub.send_all(Message(
            "Sistema",
            f"🔔 {user_name} enviou um alerta!",
            "alert_message"
        ))

    def change_status(new_status: str):
        user_name = current_user_local
        if user_name:
            logged_in_users[user_name] = new_status
            update_logged_in_users()
            page.pubsub.send_all(Message(
                "Sistema",
                f"{user_name} está agora {new_status}",
                "status_message"
            ))

    def send_message_click(e):
        if new_message.value.strip():
            page.pubsub.send_all(Message(
                current_user_local,
                new_message.value.strip(),
                "chat_message"
            ))
            new_message.value = ""
            page.update()

    async def pick_and_send_image():
        """FilePicker como serviço"""
        try:
            picker = ft.FilePicker()

            files = await picker.pick_files(
                dialog_title="Selecione uma imagem",
                file_type=ft.FilePickerFileType.IMAGE,
                allow_multiple=False,
                with_data=True,
            )

            if files and len(files) > 0:
                selected = files[0]
                if selected.bytes:
                    img_base64 = base64.b64encode(selected.bytes).decode("utf-8")
                    page.pubsub.send_all(Message(
                        current_user_local, "", "chat_message",
                        image_data=img_base64
                    ))
                    print(f"[IMAGE] ✅ Enviada: {selected.name}")
        except Exception as ex:
            print(f"[ERROR] Falha ao enviar imagem: {ex}")

    def send_image_click(e):
        page.run_task(pick_and_send_image)

    def apply_nudge_effect():
        import random
        import time
        try:
            for _ in range(6):
                page.window.left = page.window.left + random.randint(-5, 5)
                page.window.top = page.window.top + random.randint(-5, 5)
                page.update()
                time.sleep(0.05)
        except:
            pass

    def on_message(message: Message):
        if message.message_type == "login_message":
            real_user = message.original_user
            if real_user and real_user not in logged_in_users:
                logged_in_users[real_user] = "online"
                update_logged_in_users()

            if message.original_user == current_user_local:
                page.pubsub.send_all(Message(
                    "Sistema", "", "sync_request",
                    original_user=current_user_local
                ))
            elif current_user_local and current_user_local in logged_in_users:
                page.pubsub.send_all(Message(
                    "Sistema", f"👤 {current_user_local} (online)",
                    "sync_response",
                    original_user=current_user_local
                ))

            chat.controls.append(ft.Container(
                content=ft.Text(f"💬 {message.text}", italic=True,
                                color=MSN_BLUE, size=11, weight="bold"),
                padding=8,
            ))

        elif message.message_type == "sync_request":
            if current_user_local and current_user_local in logged_in_users:
                page.pubsub.send_all(Message(
                    "Sistema", f"👤 {current_user_local} (online)",
                    "sync_response",
                    original_user=current_user_local
                ))
            return

        elif message.message_type == "sync_response":
            real_user = message.original_user
            if real_user and real_user != current_user_local and real_user not in logged_in_users:
                logged_in_users[real_user] = "online"
                update_logged_in_users()
            return

        elif message.message_type == "nudge_message":
            chat.controls.append(ft.Container(
                content=ft.Text(f"⚡ {message.text}", weight="bold",
                                color=MSN_RED, size=12),
                padding=10,
                bgcolor="#FFE6E6",
                border_radius=6,
            ))
            if message.original_user != current_user_local:
                apply_nudge_effect()
        elif message.message_type == "chat_message":
            chat.controls.append(MSNMessageBubble(message, page, current_user_local))
        elif message.message_type == "alert_message":
            chat.controls.append(ft.Container(
                content=ft.Text(f"🔔 {message.text}", italic=True,
                                color=MSN_RED, size=11, weight="bold"),
                padding=8,
                bgcolor="#FFF3CD",
                border_radius=6,
            ))
        elif message.message_type == "status_message":
            chat.controls.append(ft.Container(
                content=ft.Text(f"ℹ️ {message.text}", italic=True,
                                color="#666666", size=10),
                padding=5,
            ))
        else:
            return

        page.update()

    def update_logged_in_users():
        user_list.controls.clear()
        user_list.controls.append(ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PEOPLE, size=14, color=MSN_BLUE),
                ft.Text(f"Contatos ({len(logged_in_users)})",
                        weight="bold", color=MSN_BLUE_DARK, size=12),
            ], spacing=5),
            padding=8,
            bgcolor=MSN_GRAY,
        ))

        for user, status in sorted(logged_in_users.items(),
                                   key=lambda x: (x[0] != current_user_local, x[0])):
            user_list.controls.append(UserListItem(
                user, status, is_current=(user == current_user_local)
            ))

        page.update()

    def join_chat_click(e):
        nonlocal current_user_local
        if not join_user_name.value.strip():
            join_user_name.error_text = "Digite um nome!"
            join_user_name.update()
            return

        current_user_local = join_user_name.value.strip()[:20]

        page.views.clear()
        page.views.append(main_view)

        logged_in_users[current_user_local] = "online"
        current_user_name.value = f"👤 {current_user_local}"

        page.pubsub.send_all(Message(
            "Sistema", f"➕ {current_user_local} entrou no chat!",
            "login_message",
            original_user=current_user_local
        ))
        update_logged_in_users()
        page.run_task(new_message.focus)
        page.update()

    def add_emoticon(emoticon: str):
        new_message.value += f" {emoticon} "
        page.run_task(new_message.focus)
        page.update()

    # ==================== TELA DE LOGIN ====================

    join_user_name = ft.TextField(
        label="Seu Apelido",
        autofocus=True,
        on_submit=join_chat_click,
        border_radius=6,
        width=320,
        border_color=MSN_BLUE,
        focused_border_color=MSN_BLUE_DARK,
        prefix_icon=ft.Icons.PERSON,
    )

    login_view = ft.View(
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CHAT, size=40, color=MSN_WHITE),
                            ft.Column([
                                ft.Text("MSN Conversinhas", size=28,
                                        weight="bold", color=MSN_WHITE),
                                ft.Text("Mensageiro Instantâneo",
                                        size=12, color=MSN_BLUE_LIGHT),
                            ]),
                        ], spacing=12),
                        bgcolor=MSN_BLUE,
                        padding=20,
                        width=500,
                        border_radius=ft.BorderRadius.only(top_left=10, top_right=10),
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Bem-vindo ao chat!",
                                    size=14, color="#666"),
                            ft.Container(height=20),
                            join_user_name,
                            ft.Container(height=15),
                            ft.Button(
                                content="Entrar no Chat",
                                on_click=join_chat_click,
                                bgcolor=MSN_GREEN,
                                color=MSN_WHITE,
                                width=320,
                                height=45,
                                icon=ft.Icons.LOGIN,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=6),
                                ),
                            ),
                        ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        padding=30,
                        bgcolor=MSN_WHITE,
                        width=500,
                        border_radius=ft.BorderRadius.only(bottom_left=10, bottom_right=10),
                        border=ft.Border.all(1, MSN_BORDER),
                    ),
                ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
                bgcolor=MSN_GRAY,
            )
        ],
        padding=0,
        bgcolor=MSN_GRAY,
    )

    # ==================== TELA PRINCIPAL DO CHAT ====================

    current_user_name = ft.Text("Carregando...", size=14,
                                weight="bold", color=MSN_WHITE)

    status_buttons = ft.Row([
        ft.IconButton(
            icon=ft.Icons.CIRCLE,
            tooltip="Online",
            on_click=lambda e: change_status("online"),
            icon_color=MSN_GREEN,
            icon_size=18,
        ),
        ft.IconButton(
            icon=ft.Icons.CIRCLE,
            tooltip="Ausente",
            on_click=lambda e: change_status("ausente"),
            icon_color=MSN_GOLD,
            icon_size=18,
        ),
        ft.IconButton(
            icon=ft.Icons.CIRCLE,
            tooltip="Ocupado",
            on_click=lambda e: change_status("ocupado"),
            icon_color=MSN_RED,
            icon_size=18,
        ),
    ], spacing=2)

    nudge_btn = ft.IconButton(
        icon=ft.Icons.VIBRATION,
        tooltip="Chamar atenção (Nudge!)",
        on_click=lambda e: send_nudge(current_user_local),
        icon_color=MSN_GOLD,
    )

    emoticon_buttons = ft.Row([
        ft.IconButton(
            icon=ft.Icons.SENTIMENT_VERY_SATISFIED,
            tooltip=":)", on_click=lambda e: add_emoticon(":)"),
            icon_size=20,
        ),
        ft.IconButton(
            icon=ft.Icons.SENTIMENT_DISSATISFIED,
            tooltip=":(", on_click=lambda e: add_emoticon(":("),
            icon_size=20,
        ),
        ft.IconButton(
            icon=ft.Icons.SENTIMENT_SATISFIED_ALT,
            tooltip=":D", on_click=lambda e: add_emoticon(":D"),
            icon_size=20,
        ),
        ft.IconButton(
            icon=ft.Icons.SENTIMENT_NEUTRAL,
            tooltip=":|", on_click=lambda e: add_emoticon(":|"),
            icon_size=20,
        ),
        ft.IconButton(
            icon=ft.Icons.FAVORITE,
            tooltip="<3", on_click=lambda e: add_emoticon("<3"),
            icon_size=20,
        ),
        ft.IconButton(
            icon=ft.Icons.THUMB_UP,
            tooltip="(Y)", on_click=lambda e: add_emoticon("(Y)"),
            icon_size=20,
        ),
    ], spacing=0)

    chat = ft.ListView(expand=1, spacing=10, auto_scroll=True, padding=10)
    user_list = ft.ListView(expand=1, spacing=0, auto_scroll=True)

    new_message = ft.TextField(
        hint_text="Digite uma mensagem...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=4,
        filled=True,
        expand=True,
        on_submit=send_message_click,
        border_radius=6,
        border_color=MSN_BORDER,
        focused_border_color=MSN_BLUE,
    )

    main_layout = ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHAT, size=22, color=MSN_WHITE),
                ft.Text("MSN Conversinhas", size=16,
                        weight="bold", color=MSN_WHITE),
                ft.Container(expand=True),
                ft.Text("🌐 Conectado", color=MSN_BLUE_LIGHT, size=11),
            ], spacing=8),
            bgcolor=MSN_BLUE,
            padding=10,
            border_radius=ft.BorderRadius.only(top_left=8, top_right=8),
        ),
        ft.Container(
            content=ft.Row([
                current_user_name,
                ft.Container(expand=True),
                ft.Text("Status:", weight="bold", size=11, color=MSN_BLUE_DARK),
                status_buttons,
                ft.Container(width=1, height=20, bgcolor=MSN_BORDER),
                nudge_btn,
            ], spacing=5),
            bgcolor=MSN_WHITE,
            padding=10,
            border=ft.Border.only(bottom=ft.BorderSide(1, MSN_BORDER)),
        ),
        ft.Row([
            ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.FORUM, size=14, color=MSN_BLUE),
                        ft.Text("Conversa", weight="bold",
                                color=MSN_BLUE_DARK, size=11),
                    ], spacing=5),
                    bgcolor=MSN_GRAY,
                    padding=8,
                    border=ft.Border.only(bottom=ft.BorderSide(1, MSN_BORDER)),
                ),
                ft.Container(
                    content=chat,
                    expand=True,
                    bgcolor=MSN_WHITE,
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.EMOJI_EMOTIONS,
                                size=14, color=MSN_BLUE),
                        ft.Text("Emoticons:", weight="bold",
                                color=MSN_BLUE_DARK, size=10),
                        emoticon_buttons,
                    ], spacing=5),
                    bgcolor=MSN_GRAY,
                    padding=8,
                    border=ft.Border.only(top=ft.BorderSide(1, MSN_BORDER)),
                ),
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.IMAGE,
                            tooltip="Enviar Imagem",
                            on_click=send_image_click,
                            icon_color=MSN_GREEN,
                        ),
                        new_message,
                        ft.Button(
                            content="Enviar",
                            on_click=send_message_click,
                            bgcolor=MSN_BLUE,
                            color=MSN_WHITE,
                            icon=ft.Icons.SEND,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=6),
                            ),
                        ),
                    ], spacing=5),
                    padding=10,
                    bgcolor=MSN_WHITE,
                    border=ft.Border.only(top=ft.BorderSide(1, MSN_BORDER)),
                ),
            ], expand=True, spacing=0),
            ft.Container(
                content=ft.Column([
                    user_list,
                ], spacing=0),
                width=220,
                border=ft.Border.only(left=ft.BorderSide(1, MSN_BORDER)),
                bgcolor=MSN_WHITE,
            ),
        ], expand=True, spacing=0),
    ], spacing=0, expand=True)

    main_view = ft.View(
        controls=[
            ft.Container(
                content=main_layout,
                bgcolor=MSN_WHITE,
                border=ft.Border.all(1, MSN_BORDER),
                border_radius=8,
                margin=10,
                expand=True,
            )
        ],
        padding=0,
        bgcolor=MSN_GRAY,
    )

    page.views.append(login_view)
    page.pubsub.subscribe(on_message)
    page.update()
    print("[MAIN] ✅ MSN Conversinhas iniciado!")


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)
