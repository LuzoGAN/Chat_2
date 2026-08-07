import flet as ft
import base64
import threading
import time

# 🎨 Temas disponíveis
THEMES = {
    "classico": {
        "name": "Clássico",
        "primary": "#0054A6",
        "primary_dark": "#003366",
        "primary_light": "#CCE5FF",
        "online": "#4FBA6F",
        "away": "#FFB900",
        "busy": "#E81123",
        "bg": "#F0F0F0",
        "border": "#99C9EF",
        "bubble_me": "#E8F5E9",
        "bubble_other": "#CCE5FF",
    },
    "verde": {
        "name": "Verde",
        "primary": "#00B050",
        "primary_dark": "#006630",
        "primary_light": "#E8FFE8",
        "online": "#00FF00",
        "away": "#FFD700",
        "busy": "#FF4444",
        "bg": "#F5FFF5",
        "border": "#88CC88",
        "bubble_me": "#D4FFD4",
        "bubble_other": "#E8FFE8",
    },
    "rosa": {
        "name": "Rosa",
        "primary": "#FF69B4",
        "primary_dark": "#CC3388",
        "primary_light": "#FFE8F5",
        "online": "#4FBA6F",
        "away": "#FFB900",
        "busy": "#E81123",
        "bg": "#FFF5F9",
        "border": "#FFB6D9",
        "bubble_me": "#E8F5E9",
        "bubble_other": "#FFE8F5",
    },
    "dark": {
        "name": "Dark",
        "primary": "#333333",
        "primary_dark": "#1A1A1A",
        "primary_light": "#444444",
        "online": "#00FF00",
        "away": "#FFD700",
        "busy": "#FF4444",
        "bg": "#1E1E1E",
        "border": "#555555",
        "bubble_me": "#2D4A2D",
        "bubble_other": "#3A3A3A",
    },
}

EMOTICONS = {
    ":)": "😊", ":(": "😢", ":D": "😄", ";)": "😉",
    ":P": "😜", ":/": "😕", ":O": "😮", "<3": "❤️",
    ":@": "😠", ":|": "😐", "8)": "😎", "(Y)": "👍",
    "(N)": "👎", ":$": "😳", "(H)": "😎",
}

ANIMATED_EMOTICONS = {
    ":dance": "https://media.giphy.com/media/l0HlvtIPzPdt2usKs/giphy.gif",
    ":party": "https://media.giphy.com/media/26u4cqiYI30juCOGY/giphy.gif",
    ":love": "https://media.giphy.com/media/26BRv0ThflsHCqDrG/giphy.gif",
    ":lol": "https://media.giphy.com/media/11sBLVxNs7v6WA/giphy.gif",
    ":cry": "https://media.giphy.com/media/ROF8OQvDmxytW/giphy.gif",
}

# 🔊 Sons do MSN (URLs diretas)
SOUNDS = {
    "message": "https://www.soundjay.com/buttons/sounds/button-3.mp3",
    "nudge": "https://www.soundjay.com/buttons/sounds/button-4.mp3",
    "login": "https://www.soundjay.com/buttons/sounds/button-9.mp3",
    "logout": "https://www.soundjay.com/buttons/sounds/button-10.mp3",
}


class Message:
    def __init__(self, user_name: str, text: str, message_type: str,
                 status: str = "online", image_data: str = None,
                 original_user: str = None, is_nudge: bool = False,
                 avatar_data: str = None, subnick: str = None,
                 theme: str = None, typing_user: str = None):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type
        self.status = status
        self.image_data = image_data
        self.original_user = original_user
        self.is_nudge = is_nudge
        self.avatar_data = avatar_data
        self.subnick = subnick
        self.theme = theme
        self.typing_user = typing_user

    def apply_emoticons(self, text: str) -> str:
        for emoticon, emoji in EMOTICONS.items():
            text = text.replace(emoticon, emoji)
        return text


class MSNMessageBubble(ft.Row):
    def __init__(self, message: Message, page_ref: ft.Page, current_user: str, theme: dict):
        super().__init__()
        self._page_ref = page_ref
        self.message = message
        self.current_user = current_user
        self.theme = theme
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.spacing = 8

        text = message.apply_emoticons(message.text) if message.text else ""
        is_mine = message.user_name == current_user

        bubble_color = theme["bubble_me"] if is_mine else theme["bubble_other"]
        border_color = theme["primary"] if not is_mine else theme["online"]

        bubble_content = []

        name_row = [
            ft.Text(
                f"{message.user_name} diz:" if not is_mine else "Você diz:",
                weight="bold", size=11, color=theme["primary_dark"],
            )
        ]

        if message.subnick:
            name_row.append(ft.Text(f" 🎵 {message.subnick}", size=10, color="#666666", italic=True))

        bubble_content.append(ft.Row(name_row, spacing=5))

        if message.image_data:
            img_src = f"data:image/png;base64,{message.image_data}"
            img = ft.Image(src=img_src, width=220, height=180, fit="cover", border_radius=6)
            bubble_content.append(
                ft.Container(
                    content=img,
                    on_click=lambda e: self._show_full_image(message.image_data),
                    ink=True, border_radius=6, tooltip="Clique para ampliar 🖼️",
                )
            )

        if text:
            for emoticon, gif_url in ANIMATED_EMOTICONS.items():
                if emoticon in text:
                    text = text.replace(emoticon, "")
                    bubble_content.append(ft.Image(src=gif_url, width=100, height=100))

            if text.strip():
                bubble_content.append(ft.Text(text, selectable=True, size=13, color="#000000"))

        bubble = ft.Container(
            content=ft.Column(bubble_content, spacing=4, tight=True),
            bgcolor=bubble_color, border_radius=10, padding=10,
            border=ft.Border.all(1, border_color),
        )

        if message.avatar_data:
            avatar = ft.Image(
                src=f"data:image/png;base64,{message.avatar_data}",
                width=36, height=36, border_radius=18,
            )
        else:
            avatar = ft.CircleAvatar(
                content=ft.Text(message.user_name[:1].upper(), weight="bold", size=13, color="#FFFFFF"),
                bgcolor=self._get_avatar_color(message.user_name), radius=18,
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

        img_src = f"data:image/png;base64,{image_data}"
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.IMAGE, color=self.theme["primary"]),
                ft.Text("Imagem em tamanho completo", weight="bold"),
            ]),
            content=ft.Container(
                content=ft.Image(src=img_src, width=650, height=550, fit="contain"),
                padding=10,
            ),
            actions=[ft.TextButton("Fechar", on_click=close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page_ref.overlay.append(dlg)
        dlg.open = True
        self._page_ref.update()


class UserListItem(ft.Container):
    def __init__(self, user_name: str, status: str, subnick: str = None,
                 avatar_data: str = None, is_current: bool = False, theme: dict = None):
        super().__init__()
        self.user_name = user_name
        self.status = status
        self.subnick = subnick
        self.is_current_user = is_current
        self.theme = theme or THEMES["classico"]

        status_map = {
            "online": (self.theme["online"], "Online"),
            "ausente": (self.theme["away"], "Ausente"),
            "ocupado": (self.theme["busy"], "Ocupado"),
        }
        color, label = status_map.get(status, ("#999999", "Offline"))

        user_info = [
            ft.Text(user_name, size=12, weight="bold" if is_current else "normal",
                    color=self.theme["primary_dark"], expand=True),
        ]

        if subnick:
            user_info.append(ft.Text(f"🎵 {subnick}", size=9, color="#666666", italic=True))

        if avatar_data:
            avatar = ft.Image(
                src=f"data:image/png;base64,{avatar_data}",
                width=20, height=20, border_radius=10,
            )
        else:
            avatar = ft.Icon(ft.Icons.PERSON, size=16, color=self.theme["primary_dark"])

        self.content = ft.Row([
            avatar,
            ft.Column(user_info, spacing=0, expand=True),
            ft.Container(
                content=ft.Text("●", color=color, size=10, weight="bold"),
                tooltip=label,
            ),
        ], spacing=6)
        self.padding = 8
        self.border_radius = 4
        self.bgcolor = self.theme["primary_light"] if is_current else "#FFFFFF"
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
    user_avatars = {}
    user_subnicks = {}
    current_user_local = None
    current_theme = THEMES["classico"]
    current_avatar = None
    current_subnick = None
    typing_timer = None

    # ==================== ÁUDIO ====================

    def play_sound(sound_name: str):
        """Toca som via JavaScript no navegador"""
        if sound_name not in SOUNDS:
            return

        sound_url = SOUNDS[sound_name]

        # Código JavaScript para tocar som
        js_code = f"""
        (function() {{
            try {{
                var audio = new Audio("{sound_url}");
                audio.volume = 0.5;
                var promise = audio.play();
                if (promise) {{
                    promise.catch(function(e) {{
                        console.log("Audio play blocked:", e.message);
                    }});
                }}
            }} catch(e) {{
                console.log("Audio error:", e);
            }}
        }})();
        """

        # Tenta vários métodos de executar JavaScript
        js_methods = ['run_js', 'eval_js', 'eval_javascript', 'run_javascript', 'execute_js']
        for method_name in js_methods:
            method = getattr(page, method_name, None)
            if method and callable(method):
                try:
                    method(js_code)
                    return
                except:
                    continue

    # ==================== FUNÇÕES PRINCIPAIS ====================

    def send_nudge(user_name: str):
        page.pubsub.send_all(Message(
            "Sistema", f"📢 {user_name} te chamou atenção!",
            "nudge_message", original_user=user_name, is_nudge=True
        ))

    def send_alert(user_name: str):
        page.pubsub.send_all(Message(
            "Sistema", f"🔔 {user_name} enviou um alerta!", "alert_message"
        ))

    def change_status(new_status: str):
        user_name = current_user_local
        if user_name:
            logged_in_users[user_name] = new_status
            update_logged_in_users()
            page.pubsub.send_all(Message(
                "Sistema", f"{user_name} está agora {new_status}", "status_message"
            ))

    def change_status_with_message(e):
        nonlocal current_subnick
        if status_message_input.value.strip():
            current_subnick = status_message_input.value.strip()[:50]
            user_subnicks[current_user_local] = current_subnick
            page.pubsub.send_all(Message(
                "Sistema", f"🎵 {current_user_local}: {current_subnick}",
                "status_message", subnick=current_subnick
            ))
            update_logged_in_users()

    def send_message_click(e):
        if new_message.value.strip():
            page.pubsub.send_all(Message(
                current_user_local, new_message.value.strip(),
                "chat_message", avatar_data=current_avatar, subnick=current_subnick,
            ))
            new_message.value = ""
            page.update()

    def on_text_change(e):
        if new_message.value.strip():
            page.pubsub.send_all(Message(
                "Sistema", "", "typing_indicator", typing_user=current_user_local
            ))

    async def pick_and_send_image():
        try:
            picker = ft.FilePicker()
            files = await picker.pick_files(
                dialog_title="Selecione uma imagem",
                file_type=ft.FilePickerFileType.IMAGE,
                allow_multiple=False, with_data=True,
            )
            if files and len(files) > 0:
                selected = files[0]
                if selected.bytes:
                    img_base64 = base64.b64encode(selected.bytes).decode("utf-8")
                    page.pubsub.send_all(Message(
                        current_user_local, "", "chat_message",
                        image_data=img_base64,
                        avatar_data=current_avatar, subnick=current_subnick
                    ))
        except Exception as ex:
            print(f"[ERROR] Falha ao enviar imagem: {ex}")

    def send_image_click(e):
        page.run_task(pick_and_send_image)

    async def pick_avatar():
        nonlocal current_avatar
        try:
            picker = ft.FilePicker()
            files = await picker.pick_files(
                dialog_title="Selecione seu avatar",
                file_type=ft.FilePickerFileType.IMAGE,
                allow_multiple=False, with_data=True,
            )
            if files and len(files) > 0:
                selected = files[0]
                if selected.bytes:
                    current_avatar = base64.b64encode(selected.bytes).decode("utf-8")
                    user_avatars[current_user_local] = current_avatar
                    page.pubsub.send_all(Message(
                        "Sistema", f"👤 {current_user_local} atualizou o avatar!",
                        "avatar_update", original_user=current_user_local,
                        avatar_data=current_avatar
                    ))
                    update_logged_in_users()
        except Exception as ex:
            print(f"[ERROR] Falha ao atualizar avatar: {ex}")

    def change_avatar_click(e):
        page.run_task(pick_avatar)

    def change_theme_click(e):
        theme_menu.open = True
        page.update()

    def apply_theme(theme_name: str):
        nonlocal current_theme
        current_theme = THEMES[theme_name]
        theme_menu.open = False
        page.pubsub.send_all(Message(
            "Sistema", f"🎨 {current_user_local} mudou para o tema {current_theme['name']}!",
            "theme_change", original_user=current_user_local, theme=theme_name
        ))
        page.update()

    def close_theme_menu(e):
        theme_menu.open = False
        page.update()

    def apply_nudge_effect():
        """Tremor de janela - clássico do MSN"""
        import random
        try:
            original_left = page.window.left
            original_top = page.window.top
            for _ in range(6):
                page.window.left = original_left + random.randint(-5, 5)
                page.window.top = original_top + random.randint(-5, 5)
                page.update()
                time.sleep(0.05)
            page.window.left = original_left
            page.window.top = original_top
            page.update()
        except:
            pass

    def clear_typing_indicator():
        nonlocal typing_timer
        try:
            typing_label.value = ""
            page.update()
        except:
            pass
        if typing_timer:
            typing_timer.cancel()
            typing_timer = None

    def schedule_typing_clear():
        nonlocal typing_timer
        if typing_timer:
            typing_timer.cancel()
        typing_timer = threading.Timer(3.0, clear_typing_indicator)
        typing_timer.start()

    def on_disconnect(e):
        if current_user_local:
            page.pubsub.send_all(Message(
                "Sistema", f"👋 {current_user_local} saiu do chat",
                "logout_message", original_user=current_user_local
            ))
            if current_user_local in logged_in_users:
                del logged_in_users[current_user_local]

    def on_message(message: Message):
        if message.message_type == "login_message":
            real_user = message.original_user
            if real_user and real_user not in logged_in_users:
                logged_in_users[real_user] = "online"
                if message.avatar_data:
                    user_avatars[real_user] = message.avatar_data
                if message.subnick:
                    user_subnicks[real_user] = message.subnick
                update_logged_in_users()
                play_sound("login")

            if message.original_user == current_user_local:
                page.pubsub.send_all(Message(
                    "Sistema", "", "sync_request",
                    original_user=current_user_local,
                    avatar_data=current_avatar, subnick=current_subnick
                ))
            elif current_user_local and current_user_local in logged_in_users:
                page.pubsub.send_all(Message(
                    "Sistema", f"👤 {current_user_local} (online)",
                    "sync_response", original_user=current_user_local,
                    avatar_data=current_avatar, subnick=current_subnick
                ))

            chat.controls.append(ft.Container(
                content=ft.Text(f"💬 {message.text}", italic=True,
                                color=current_theme["primary"], size=11, weight="bold"),
                padding=8,
            ))

        elif message.message_type == "logout_message":
            real_user = message.original_user
            if real_user and real_user in logged_in_users:
                del logged_in_users[real_user]
                update_logged_in_users()
                play_sound("logout")

            chat.controls.append(ft.Container(
                content=ft.Text(f"👋 {message.text}", italic=True,
                                color="#999999", size=11),
                padding=8,
            ))

        elif message.message_type == "sync_request":
            if current_user_local and current_user_local in logged_in_users:
                page.pubsub.send_all(Message(
                    "Sistema", f"👤 {current_user_local} (online)",
                    "sync_response", original_user=current_user_local,
                    avatar_data=current_avatar, subnick=current_subnick
                ))
            return

        elif message.message_type == "sync_response":
            real_user = message.original_user
            if real_user and real_user != current_user_local and real_user not in logged_in_users:
                logged_in_users[real_user] = "online"
                if message.avatar_data:
                    user_avatars[real_user] = message.avatar_data
                if message.subnick:
                    user_subnicks[real_user] = message.subnick
                update_logged_in_users()
            return

        elif message.message_type == "nudge_message":
            chat.controls.append(ft.Container(
                content=ft.Text(f"⚡ {message.text}", weight="bold",
                                color=current_theme["busy"], size=12),
                padding=10, bgcolor="#FFE6E6", border_radius=6,
            ))
            play_sound("nudge")
            if message.original_user != current_user_local:
                apply_nudge_effect()

        elif message.message_type == "typing_indicator":
            if message.typing_user and message.typing_user != current_user_local:
                typing_label.value = f"{message.typing_user} está digitando..."
                page.update()
                schedule_typing_clear()
            return

        elif message.message_type == "avatar_update":
            if message.original_user:
                user_avatars[message.original_user] = message.avatar_data
                update_logged_in_users()
            chat.controls.append(ft.Container(
                content=ft.Text(f"👤 {message.text}", italic=True,
                                color="#666666", size=10),
                padding=5,
            ))

        elif message.message_type == "theme_change":
            chat.controls.append(ft.Container(
                content=ft.Text(f"🎨 {message.text}", italic=True,
                                color="#666666", size=10),
                padding=5,
            ))

        elif message.message_type == "chat_message":
            chat.controls.append(MSNMessageBubble(message, page, current_user_local, current_theme))
            if message.user_name != current_user_local:
                play_sound("message")

        elif message.message_type == "alert_message":
            chat.controls.append(ft.Container(
                content=ft.Text(f"🔔 {message.text}", italic=True,
                                color=current_theme["busy"], size=11, weight="bold"),
                padding=8, bgcolor="#FFF3CD", border_radius=6,
            ))
            play_sound("message")

        elif message.message_type == "status_message":
            chat.controls.append(ft.Container(
                content=ft.Text(f"ℹ️ {message.text}", italic=True,
                                color="#666666", size=10),
                padding=5,
            ))
            if message.original_user and message.subnick:
                user_subnicks[message.original_user] = message.subnick
                update_logged_in_users()
        else:
            return

        page.update()

    def update_logged_in_users():
        user_list.controls.clear()
        user_list.controls.append(ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PEOPLE, size=14, color=current_theme["primary"]),
                ft.Text(f"Contatos ({len(logged_in_users)})",
                        weight="bold", color=current_theme["primary_dark"], size=12),
            ], spacing=5),
            padding=8, bgcolor=current_theme["bg"],
        ))

        for user, status in sorted(logged_in_users.items(),
                                   key=lambda x: (x[0] != current_user_local, x[0])):
            user_list.controls.append(UserListItem(
                user, status,
                subnick=user_subnicks.get(user),
                avatar_data=user_avatars.get(user),
                is_current=(user == current_user_local),
                theme=current_theme
            ))
        page.update()

    def join_chat_click(e):
        nonlocal current_user_local
        if not join_user_name.value.strip():
            join_user_name.error_text = "Digite um nome!"
            join_user_name.update()
            return

        current_user_local = join_user_name.value.strip()[:20]
        page.on_disconnect = on_disconnect
        page.views.clear()
        page.views.append(main_view)

        logged_in_users[current_user_local] = "online"
        current_user_name.value = f"👤 {current_user_local}"

        page.pubsub.send_all(Message(
            "Sistema", f"➕ {current_user_local} entrou no chat!",
            "login_message", original_user=current_user_local,
            avatar_data=current_avatar, subnick=current_subnick
        ))
        update_logged_in_users()
        play_sound("login")
        page.update()

    def add_emoticon(emoticon: str):
        new_message.value += f" {emoticon} "
        page.update()

    # ==================== TELA DE LOGIN ====================

    join_user_name = ft.TextField(
        label="Seu Apelido", autofocus=True, on_submit=join_chat_click,
        border_radius=6, width=320, border_color="#0054A6",
        focused_border_color="#003366", prefix_icon=ft.Icons.PERSON,
    )

    login_view = ft.View(
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CHAT, size=40, color="#FFFFFF"),
                            ft.Column([
                                ft.Text("MSN Conversinhas", size=28,
                                        weight="bold", color="#FFFFFF"),
                                ft.Text("Mensageiro Instantâneo",
                                        size=12, color="#CCE5FF"),
                            ]),
                        ], spacing=12),
                        bgcolor="#0054A6", padding=20, width=500,
                        border_radius=ft.BorderRadius.only(top_left=10, top_right=10),
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Bem-vindo ao chat!", size=14, color="#666"),
                            ft.Container(height=20),
                            join_user_name,
                            ft.Container(height=15),
                            ft.Button(
                                content="Entrar no Chat", on_click=join_chat_click,
                                bgcolor="#4FBA6F", color="#FFFFFF",
                                width=320, height=45, icon=ft.Icons.LOGIN,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                            ),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                        padding=30, bgcolor="#FFFFFF", width=500,
                        border_radius=ft.BorderRadius.only(bottom_left=10, bottom_right=10),
                        border=ft.Border.all(1, "#99C9EF"),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                alignment=ft.Alignment.CENTER, expand=True, bgcolor="#F0F0F0",
            )
        ],
        padding=0, bgcolor="#F0F0F0",
    )

    # ==================== TELA PRINCIPAL DO CHAT ====================

    current_user_name = ft.Text("Carregando...", size=14, weight="bold", color="#FFFFFF")

    status_message_input = ft.TextField(
        hint_text="🎵 No que está pensando? (subnick)",
        width=300, border_radius=6, on_submit=change_status_with_message,
    )

    status_buttons = ft.Row([
        ft.IconButton(icon=ft.Icons.CIRCLE, tooltip="Online",
                      on_click=lambda e: change_status("online"),
                      icon_color=current_theme["online"], icon_size=18),
        ft.IconButton(icon=ft.Icons.CIRCLE, tooltip="Ausente",
                      on_click=lambda e: change_status("ausente"),
                      icon_color=current_theme["away"], icon_size=18),
        ft.IconButton(icon=ft.Icons.CIRCLE, tooltip="Ocupado",
                      on_click=lambda e: change_status("ocupado"),
                      icon_color=current_theme["busy"], icon_size=18),
    ], spacing=2)

    nudge_btn = ft.IconButton(
        icon=ft.Icons.VIBRATION, tooltip="Chamar atenção (Nudge!)",
        on_click=lambda e: send_nudge(current_user_local),
        icon_color=current_theme["away"],
    )

    avatar_btn = ft.IconButton(
        icon=ft.Icons.ACCOUNT_CIRCLE, tooltip="Mudar Avatar",
        on_click=change_avatar_click, icon_color=current_theme["primary"],
    )

    theme_btn = ft.IconButton(
        icon=ft.Icons.PALETTE, tooltip="Mudar Tema",
        on_click=change_theme_click, icon_color=current_theme["primary"],
    )

    theme_menu = ft.AlertDialog(
        title=ft.Text("Escolha um Tema", weight="bold"),
        content=ft.Container(
            width=300,
            content=ft.Column([
                ft.ListTile(leading=ft.Icon(ft.Icons.CHAT, color="#0054A6"),
                            title=ft.Text("Clássico"),
                            on_click=lambda e: apply_theme("classico")),
                ft.ListTile(leading=ft.Icon(ft.Icons.CHAT, color="#00B050"),
                            title=ft.Text("Verde"),
                            on_click=lambda e: apply_theme("verde")),
                ft.ListTile(leading=ft.Icon(ft.Icons.CHAT, color="#FF69B4"),
                            title=ft.Text("Rosa"),
                            on_click=lambda e: apply_theme("rosa")),
                ft.ListTile(leading=ft.Icon(ft.Icons.CHAT, color="#333333"),
                            title=ft.Text("Dark"),
                            on_click=lambda e: apply_theme("dark")),
            ], tight=True)
        ),
        actions=[ft.TextButton("Cancelar", on_click=close_theme_menu)],
    )

    emoticon_buttons = ft.Row([
        ft.IconButton(icon=ft.Icons.SENTIMENT_VERY_SATISFIED, tooltip=":)",
                      on_click=lambda e: add_emoticon(":)"), icon_size=20),
        ft.IconButton(icon=ft.Icons.SENTIMENT_DISSATISFIED, tooltip=":(",
                      on_click=lambda e: add_emoticon(":("), icon_size=20),
        ft.IconButton(icon=ft.Icons.SENTIMENT_SATISFIED_ALT, tooltip=":D",
                      on_click=lambda e: add_emoticon(":D"), icon_size=20),
        ft.IconButton(icon=ft.Icons.FAVORITE, tooltip="<3",
                      on_click=lambda e: add_emoticon("<3"), icon_size=20),
        ft.IconButton(icon=ft.Icons.THUMB_UP, tooltip="(Y)",
                      on_click=lambda e: add_emoticon("(Y)"), icon_size=20),
        ft.TextButton(content="🎭 :dance", tooltip="Dança",
                      on_click=lambda e: add_emoticon(":dance")),
        ft.TextButton(content="🎉 :party", tooltip="Festa",
                      on_click=lambda e: add_emoticon(":party")),
        ft.TextButton(content="😂 :lol", tooltip="Risada",
                      on_click=lambda e: add_emoticon(":lol")),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)

    chat = ft.ListView(expand=1, spacing=10, auto_scroll=True, padding=10)
    user_list = ft.ListView(expand=1, spacing=0, auto_scroll=True)
    typing_label = ft.Text("", size=10, color="#666666", italic=True)

    new_message = ft.TextField(
        hint_text="Digite uma mensagem...", autofocus=True, shift_enter=True,
        min_lines=1, max_lines=4, filled=True, expand=True,
        on_submit=send_message_click, on_change=on_text_change,
        border_radius=6, border_color=current_theme["border"],
        focused_border_color=current_theme["primary"],
    )

    main_layout = ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHAT, size=22, color="#FFFFFF"),
                ft.Text("MSN Conversinhas", size=16, weight="bold", color="#FFFFFF"),
                ft.Container(expand=True),
                ft.Text("🌐 Conectado", color="#CCE5FF", size=11),
            ], spacing=8),
            bgcolor=current_theme["primary"], padding=10,
            border_radius=ft.BorderRadius.only(top_left=8, top_right=8),
        ),
        ft.Container(
            content=ft.Column([
                ft.Row([
                    current_user_name, ft.Container(expand=True),
                    ft.Text("Status:", weight="bold", size=11, color=current_theme["primary_dark"]),
                    status_buttons,
                    ft.Container(width=1, height=20, bgcolor=current_theme["border"]),
                    avatar_btn, theme_btn, nudge_btn,
                ], spacing=5),
                status_message_input,
            ], spacing=5),
            bgcolor="#FFFFFF", padding=10,
            border=ft.Border.only(bottom=ft.BorderSide(1, current_theme["border"])),
        ),
        ft.Row([
            ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.FORUM, size=14, color=current_theme["primary"]),
                        ft.Text("Conversa", weight="bold",
                                color=current_theme["primary_dark"], size=11),
                    ], spacing=5),
                    bgcolor=current_theme["bg"], padding=8,
                    border=ft.Border.only(bottom=ft.BorderSide(1, current_theme["border"])),
                ),
                ft.Container(content=chat, expand=True, bgcolor="#FFFFFF"),
                ft.Container(
                    content=typing_label,
                    padding=ft.Padding.only(left=10, top=2, bottom=2),
                    bgcolor=current_theme["bg"],
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.EMOJI_EMOTIONS, size=14, color=current_theme["primary"]),
                        ft.Text("Emoticons:", weight="bold",
                                color=current_theme["primary_dark"], size=10),
                        emoticon_buttons,
                    ], spacing=5),
                    bgcolor=current_theme["bg"], padding=8,
                    border=ft.Border.only(top=ft.BorderSide(1, current_theme["border"])),
                ),
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(icon=ft.Icons.IMAGE, tooltip="Enviar Imagem",
                                      on_click=send_image_click,
                                      icon_color=current_theme["online"]),
                        new_message,
                        ft.Button(
                            content="Enviar", on_click=send_message_click,
                            bgcolor=current_theme["primary"], color="#FFFFFF",
                            icon=ft.Icons.SEND,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                        ),
                    ], spacing=5),
                    padding=10, bgcolor="#FFFFFF",
                    border=ft.Border.only(top=ft.BorderSide(1, current_theme["border"])),
                ),
            ], expand=True, spacing=0),
            ft.Container(
                content=ft.Column([user_list], spacing=0),
                width=220,
                border=ft.Border.only(left=ft.BorderSide(1, current_theme["border"])),
                bgcolor="#FFFFFF",
            ),
        ], expand=True, spacing=0),
    ], spacing=0, expand=True)

    main_view = ft.View(
        controls=[
            ft.Container(
                content=main_layout, bgcolor="#FFFFFF",
                border=ft.Border.all(1, current_theme["border"]),
                border_radius=8, margin=10, expand=True,
            )
        ],
        padding=0, bgcolor=current_theme["bg"],
    )

    page.views.append(login_view)
    page.pubsub.subscribe(on_message)
    page.update()
    print("[MAIN] ✅ MSN Conversinhas iniciado!")


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)
