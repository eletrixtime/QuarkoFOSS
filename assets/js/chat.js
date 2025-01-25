//Thank GPT for helping me to make this!
var notif = new Audio('../../../../../assets/sounds/notif.mp3');
var CDN_URL = "{{ CDN_URL }}";
console.log("[Quarko-SocketIO] Chat JS loaded ! (v1)")
function log(text){
    console.log("[Quarko-SocketIO] " + text)
}
var socket = io();
        socket.on('connect', function() {
        log("Connected !");
        //socket.emit('join', { token: '{{ token }}', room: 'public-1' });
        log("Connect testing")
});

socket.on('disconnect', function() {
    log("Connection lost...");
    show_popup("<h1>Connexion Perdue...</h1> <br> <p>La connexion a été perdue</p> <button onclick='location.reload()'>Raffraichir la page</button>");
});
function sendMessage(token,room) {
    var message = document.getElementById('messageInput').value;
    if (message.length < 1) {
        show_popup("<h1>Merci de saisir un message !</h1> <br> <p>Ohoh ! envoie un message pas de truc vide !</p> <p>Clique n'importe ou pour fermer</p>");
        
        return;
    }
    else{
        if (message.length > 200) {
            show_popup("Merci de ne pas envoyer de message trop long ! (limite 200 caractères)");
            return;
        }
        socket.emit('send_message', { message: message, token: token ,room: room });
        log("Sended message :" + message)
        document.getElementById('messageInput').value = '';
    }

}
function joinRoom(room,token) {
    socket.emit('join', {'token': token, 'room': room});
}
socket.on('send_message', function(data) {
    var message = `${data.username}: ${data.message}`;
    console.log(data.admin);
    var messagesDiv = document.getElementById("messages");
    var msgElement = document.createElement("div");
    msgElement.classList.add("message-container");
    
    var imgElement = document.createElement("img");
    imgElement.src = "" + data.pp;
    imgElement.classList.add("profile-image");
    
    var textElement = document.createElement("div");
    textElement.textContent = message;
    
    if (data.username == "eletrixtimelevrai" || data.username == "l-s") {
        console.log("staff ok");
        textElement.classList.add("message-text-admin");
    } else {
        console.log("staff no");
        textElement.classList.add("message-text");
    }
    
    msgElement.appendChild(imgElement);
    msgElement.appendChild(textElement);
    
    messagesDiv.appendChild(msgElement);
    notif.play();

});
socket.on('update_connected', function(data) {
    console.log(data.update_connected);
    document.getElementById("connected").innerHTML = "connecters : " + data.update_connected;
});

socket.emit('join', { token: '{{ token }}', room: 'public-1' });