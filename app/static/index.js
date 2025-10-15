// Получаем данные из скрытого элемента
const roomData = document.getElementById("room-data");
const roomId = roomData.getAttribute("data-room-id");
const username = roomData.getAttribute("data-username");
const userId = roomData.getAttribute("data-user-id");

// Создаем WebSocket соединение
const ws = new WebSocket(`ws://127.0.0.1:8000/ws/chat/${roomId}/${userId}?username=${encodeURIComponent(username)}`);

// Обрабатываем входящие сообщения
ws.onmessage = (event) => {
    const messages = document.getElementById("messages");
    const messageData = JSON.parse(event.data);
    const message = document.createElement("div");

    // Определяем стили в зависимости от отправителя
    if (messageData.is_self) {
        message.className = "p-2 my-1 bg-blue-500 text-white rounded-md self-end max-w-xs ml-auto flex justify-between items-center";
    } else {
        message.className = "p-2 my-1 bg-gray-200 text-black rounded-md self-start max-w-xs flex justify-between items-center";
    }

    message.innerHTML = `<span>${messageData.text}</span><span class="text-xs ${messageData.is_self ? 'text-gray-300' : 'text-gray-500'} ml-auto">${messageData.timestamp || ''}</span>`;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
};

// Отправка сообщений
function sendMessage() {
    const input = document.getElementById("messageInput");
    if (input.value.trim()) {
        ws.send(input.value);
        input.value = '';
    }
}

// Добавляем отправку по Enter
document.getElementById("messageInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendMessage();
    }
});

// Обработка состояния соединения
ws.onopen = () => {
    console.log("✅ Соединение установлено");
};

ws.onclose = (event) => {
    console.log("❌ Соединение закрыто", event.code, event.reason);
};

ws.onerror = (error) => {
    console.error("🔴 Ошибка WebSocket:", error);
    console.log("Попробуйте:");
    console.log("1. Перезапустить сервер");
    console.log("2. Проверить антивирус/файрвол");
    console.log("3. Открыть браузер от администратора");
};