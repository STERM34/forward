import customtkinter as ctk
import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.tl.types import InputPeerUser, InputPeerChannel, InputPeerChannelFromMessage, InputPeerUserFromMessage
from telethon.tl.functions.contacts import ImportContactsRequest, SearchRequest
from telethon.tl.types import InputPhoneContact, InputMessagesFilterEmpty
import json
import os
from datetime import datetime
import threading
import time
import re
import tkinter as tk
import pyperclip
import nest_asyncio
from urllib.parse import urlparse, parse_qs

nest_asyncio.apply()

class CustomEntry(ctk.CTkEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind("<Button-3>", self.show_context_menu)
        self.bind("<Control-v>", self.paste)
        self.bind("<Control-V>", self.paste)
    def show_context_menu(self, event):
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Вставить", command=self.paste)
        context_menu.add_command(label="Копировать", command=self.copy)
        context_menu.add_command(label="Вырезать", command=self.cut)
        context_menu.post(event.x_root, event.y_root)
    def paste(self, event=None):
        try:
            clipboard_text = pyperclip.paste()
            try:
                self.delete("sel.first", "sel.last")
            except:
                pass
            self.insert("insert", clipboard_text)
        except Exception as e:
            print(f"Ошибка при вставке: {e}")
    def copy(self):
        try:
            selected_text = self.selection_get()
            pyperclip.copy(selected_text)
        except:
            pass
    def cut(self):
        try:
            self.copy()
            self.delete("sel.first", "sel.last")
        except:
            pass

class CustomTextbox(ctk.CTkTextbox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind("<Button-3>", self.show_context_menu)
        self.bind("<Control-v>", self.paste)
        self.bind("<Control-V>", self.paste)
    def show_context_menu(self, event):
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Вставить", command=self.paste)
        context_menu.add_command(label="Копировать", command=self.copy)
        context_menu.add_command(label="Вырезать", command=self.cut)
        context_menu.post(event.x_root, event.y_root)
    def paste(self, event=None):
        try:
            clipboard_text = pyperclip.paste()
            try:
                self.delete("sel.first", "sel.last")
            except:
                pass
            self.insert("insert", clipboard_text)
        except Exception as e:
            print(f"Ошибка при вставке: {e}")
    def copy(self):
        try:
            selected_text = self.selection_get()
            pyperclip.copy(selected_text)
        except:
            pass
    def cut(self):
        try:
            self.copy()
            self.delete("sel.first", "sel.last")
        except:
            pass

class MessageForwarder(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Пересылка сообщений Telegram")
        self.geometry("800x600")
        self.api_id = ctk.StringVar()
        self.api_hash = ctk.StringVar()
        self.phone = ctk.StringVar()
        self.interval = ctk.StringVar(value="60")
        self.verification_code = ctk.StringVar()
        self.create_widgets()
        self.client = None
        self.is_connected = False
        self.verification_dialog = None
        self.forward_message = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.load_contacts()
    def create_widgets(self):
        auth_frame = ctk.CTkFrame(self)
        auth_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(auth_frame, text="API ID:").pack(side="left", padx=5)
        self.api_id_entry = CustomEntry(auth_frame, textvariable=self.api_id, width=100)
        self.api_id_entry.pack(side="left", padx=5)
        ctk.CTkLabel(auth_frame, text="API Hash:").pack(side="left", padx=5)
        self.api_hash_entry = CustomEntry(auth_frame, textvariable=self.api_hash, width=200)
        self.api_hash_entry.pack(side="left", padx=5)
        ctk.CTkLabel(auth_frame, text="Телефон:").pack(side="left", padx=5)
        self.phone_entry = CustomEntry(auth_frame, textvariable=self.phone, width=150)
        self.phone_entry.pack(side="left", padx=5)
        ctk.CTkButton(auth_frame, text="Подключиться", command=self.connect_telegram).pack(side="left", padx=5)
        interval_frame = ctk.CTkFrame(self)
        interval_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(interval_frame, text="Интервал (секунды):").pack(side="left", padx=5)
        self.interval_entry = CustomEntry(interval_frame, textvariable=self.interval, width=100)
        self.interval_entry.pack(side="left", padx=5)
        messages_frame = ctk.CTkFrame(self)
        messages_frame.pack(pady=10, padx=10, fill="both", expand=True)
        ctk.CTkLabel(messages_frame, text="Текст нового сообщения:").pack(pady=5)
        self.message_text = CustomTextbox(messages_frame, height=200)
        self.message_text.pack(pady=5, padx=5, fill="both", expand=True)
        contacts_frame = ctk.CTkFrame(self)
        contacts_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(contacts_frame, text="Контакты (номера телефонов, ID Telegram или @username, по одному на строку):").pack(pady=5)
        self.contacts_text = CustomTextbox(contacts_frame, height=100)
        self.contacts_text.pack(pady=5, padx=5, fill="both", expand=True)
        contacts_buttons_frame = ctk.CTkFrame(contacts_frame)
        contacts_buttons_frame.pack(pady=5, fill="x")
        ctk.CTkButton(contacts_buttons_frame, text="Сохранить контакты", command=self.save_contacts).pack(side="left", padx=5)
        ctk.CTkButton(contacts_buttons_frame, text="Очистить контакты", command=self.clear_contacts).pack(side="left", padx=5)
        ctk.CTkButton(self, text="Начать отправку", command=self.start_sending).pack(pady=10)
    def show_verification_dialog(self):
        if self.verification_dialog is None:
            self.verification_dialog = ctk.CTkToplevel(self)
            self.verification_dialog.title("Код подтверждения")
            self.verification_dialog.geometry("300x150")
            ctk.CTkLabel(self.verification_dialog, text="Введите код подтверждения:").pack(pady=10)
            self.verification_entry = CustomEntry(self.verification_dialog, textvariable=self.verification_code)
            self.verification_entry.pack(pady=5)
            ctk.CTkButton(self.verification_dialog, text="Подтвердить", 
                         command=self.submit_verification_code).pack(pady=5)
    def submit_verification_code(self):
        if self.verification_dialog:
            self.verification_dialog.destroy()
            self.verification_dialog = None
            self.loop.run_until_complete(self.complete_verification())
    async def complete_verification(self):
        try:
            await self.client.sign_in(self.phone.get(), self.verification_code.get())
            self.is_connected = True
            print("Успешное подключение к Telegram")
        except Exception as e:
            print(f"Ошибка при верификации: {e}")
    async def setup_message_handler(self):
        @self.client.on(events.NewMessage(pattern='/forward'))
        async def forward_handler(event):
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                self.forward_message = reply_msg
                contacts_text = self.contacts_text.get("1.0", "end-1c").strip()
                if not contacts_text:
                    await event.respond("Сначала добавьте контакты в программу")
                    return
                contacts = [self.parse_contact(c.strip()) for c in contacts_text.split("\n")]
                contacts = [c for c in contacts if c is not None]
                if not contacts:
                    await event.respond("Не удалось распознать контакты")
                    return
                for contact in contacts:
                    try:
                        await self.try_forward_or_send(contact, reply_msg)
                    except Exception as e:
                        print(f"Ошибка при пересылке для {contact['value']}: {e}")
            else:
                await event.respond("Ответьте на сообщение командой /forward, чтобы сохранить и переслать его")
    async def connect_telegram_client(self):
        try:
            self.client = TelegramClient('session_name', self.api_id.get(), self.api_hash.get())
            await self.client.connect()
            if not await self.client.is_user_authorized():
                await self.client.send_code_request(self.phone.get())
                self.show_verification_dialog()
            else:
                self.is_connected = True
                print("Уже авторизован")
                await self.setup_message_handler()
            return True
        except Exception as e:
            print(f"Ошибка подключения к Telegram: {e}")
            return False
    def connect_telegram(self):
        self.loop.run_until_complete(self.connect_telegram_client())
    def parse_contact(self, contact):
        contact = contact.strip()
        if contact.startswith('@'):
            username = contact[1:].strip()
            if username:
                return {'type': 'username', 'value': username}
        contact = re.sub(r'[^\d+]', '', contact)
        if re.match(r'^\d+$', contact):
            if len(contact) >= 8:
                return {'type': 'id', 'value': int(contact)}
        if re.match(r'^\+?[0-9]{10,15}$', contact):
            if not contact.startswith('+'):
                if contact.startswith('7') or contact.startswith('8'):
                    contact = '+7' + contact[1:]
                elif contact.startswith('380'):
                    contact = '+' + contact
                else:
                    contact = '+' + contact
            return {'type': 'phone', 'value': contact}
        print(f"Не удалось определить тип контакта: {contact}")
        return None
    async def get_peer(self, contact):
        try:
            if contact['type'] == 'phone':
                phone = contact['value']
                print(f"Поиск пользователя по номеру телефона: {phone}")
                try:
                    user = await self.client.get_entity(phone)
                    print(f"Пользователь найден через get_entity: {user.id}")
                    return user
                except Exception as e:
                    print(f"Не удалось найти через get_entity: {e}")
                    try:
                        phone_variants = [
                            phone,
                            phone.replace('+7', '+8'),
                            phone.replace('+8', '+7'),
                            phone[1:] if phone.startswith('+') else phone,
                            '+' + phone if not phone.startswith('+') else phone
                        ]
                        for variant in phone_variants:
                            try:
                                print(f"Пробуем импортировать контакт с номером: {variant}")
                                contact_obj = InputPhoneContact(
                                    client_id=0,
                                    phone=variant,
                                    first_name="User",
                                    last_name=""
                                )
                                result = await self.client(ImportContactsRequest([contact_obj]))
                                if result.users:
                                    print(f"Контакт успешно импортирован: {result.users[0].id}")
                                    return result.users[0]
                            except Exception as e:
                                print(f"Ошибка при импорте варианта {variant}: {e}")
                                continue
                        print("Все варианты номера не удалось импортировать")
                        return None
                    except Exception as e:
                        print(f"Ошибка импорта контакта {phone}: {e}")
                        return None
            elif contact['type'] == 'username':
                username = contact['value']
                print(f"Поиск пользователя по username: @{username}")
                try:
                    user = await self.client.get_entity(username)
                    print(f"Пользователь найден через get_entity: {user.id}")
                    return user
                except Exception as e:
                    print(f"Не удалось найти пользователя по username @{username}: {e}")
                    return None
            else:
                print(f"Поиск пользователя по Telegram ID: {contact['value']}")
                try:
                    print("Пробуем поиск через SearchRequest...")
                    result = await self.client(SearchRequest(
                        q=str(contact['value']),
                        limit=1
                    ))
                    if result.users:
                        print(f"Пользователь найден через поиск: {result.users[0].id}")
                        return result.users[0]
                    else:
                        print("Пользователь не найден через поиск")
                except Exception as e:
                    print(f"Ошибка поиска: {e}")
                try:
                    print("Пробуем создать InputPeerUser...")
                    return InputPeerUser(contact['value'], 0)
                except Exception as e:
                    print(f"Ошибка создания InputPeerUser: {e}")
                    try:
                        print("Пробуем найти через get_entity...")
                        user = await self.client.get_entity(contact['value'])
                        print(f"Пользователь найден через get_entity: {user.id}")
                        return user
                    except Exception as e:
                        print(f"Не удалось найти через get_entity: {e}")
                        return None
        except Exception as e:
            print(f"Ошибка получения peer для {contact['value']}: {e}")
            return None
    async def try_forward_or_send(self, contact, message_or_text):
        try:
            peer = await self.get_peer(contact)
            if not peer:
                print(f"Не удалось найти пользователя {contact['value']}")
                return False
            if hasattr(message_or_text, 'id'):
                try:
                    print(f"Пробуем переслать сообщение {message_or_text.id} пользователю {contact['value']}")
                    await self.client.forward_messages(
                        peer,
                        message_or_text,
                        from_peer='me',
                        silent=True
                    )
                    print(f"Сообщение успешно переслано пользователю {contact['value']}")
                    return True
                except Exception as e:
                    print(f"Ошибка при пересылке сообщения: {e}")
                    if message_or_text.text:
                        print(f"Пробуем отправить как новое сообщение пользователю {contact['value']}")
                        try:
                            await self.client.send_message(
                                peer,
                                message_or_text.text,
                                silent=True
                            )
                            if message_or_text.media:
                                print("Отправляем медиа отдельно...")
                                await self.client.send_file(
                                    peer,
                                    message_or_text.media,
                                    silent=True
                                )
                            print(f"Сообщение отправлено как новое пользователю {contact['value']}")
                            return True
                        except Exception as e:
                            print(f"Ошибка при отправке нового сообщения: {e}")
                            return False
            else:
                print(f"Отправляем новое сообщение пользователю {contact['value']}")
                try:
                    await self.client.send_message(
                        peer,
                        message_or_text,
                        silent=True
                    )
                    print(f"Сообщение отправлено как новое пользователю {contact['value']}")
                    return True
                except Exception as e:
                    print(f"Ошибка при отправке нового сообщения: {e}")
                    return False
        except Exception as e:
            print(f"Ошибка при обработке сообщения для {contact['value']}: {e}")
            return False
    def start_sending(self):
        if not self.is_connected:
            print("Сначала подключитесь к Telegram")
            return
        contacts = [self.parse_contact(c.strip()) for c in self.contacts_text.get("1.0", "end-1c").strip().split("\n")]
        contacts = [c for c in contacts if c is not None]
        new_message = self.message_text.get("1.0", "end-1c").strip()
        messages = []
        if self.forward_message:
            messages.append(self.forward_message)
        if new_message:
            messages.append(new_message)
        if not messages:
            print("Нет сообщений для отправки")
            return
        interval = int(self.interval.get())
        threading.Thread(target=self.process_messages, 
                       args=(contacts, messages, interval),
                       daemon=True).start()
    def process_messages(self, contacts, messages, interval):
        async def process_all():
            for contact in contacts:
                try:
                    for message in messages:
                        success = await self.try_forward_or_send(contact, message)
                        if success:
                            print(f"Успешно обработано сообщение для {contact['value']}")
                        await asyncio.sleep(interval)
                except Exception as e:
                    print(f"Ошибка обработки сообщений для {contact['value']}: {e}")
        self.loop.run_until_complete(process_all())
    def save_contacts(self):
        try:
            contacts = self.contacts_text.get("1.0", "end-1c").strip()
            with open("contacts.txt", "w", encoding="utf-8") as f:
                f.write(contacts)
            print("Контакты сохранены")
        except Exception as e:
            print(f"Ошибка при сохранении контактов: {e}")
    def load_contacts(self):
        try:
            if os.path.exists("contacts.txt"):
                with open("contacts.txt", "r", encoding="utf-8") as f:
                    contacts = f.read()
                self.contacts_text.delete("1.0", "end")
                self.contacts_text.insert("1.0", contacts)
                print("Контакты загружены")
        except Exception as e:
            print(f"Ошибка при загрузке контактов: {e}")
    def clear_contacts(self):
        self.contacts_text.delete("1.0", "end")
        print("Контакты очищены")

if __name__ == "__main__":
    app = MessageForwarder()
    app.mainloop() 