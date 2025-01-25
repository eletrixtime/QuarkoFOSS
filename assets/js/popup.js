
function show_popup(html) {
        var overlay = document.getElementById('popup-overlay');
        var content = document.getElementById('popup-content');
        var audio = new Audio('../../../../../assets/sounds/error.mp3');
        audio.play();
        content.innerHTML = html;
        overlay.style.display = 'flex';
        overlay.onclick = function() {
            overlay.style.display = 'none';
        };
    }
