function getTypeFromExtension(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    
    switch (extension) {
        case 'png':
        case 'jpg':
        case 'jpeg':
        case 'gif':
            return 'image';
        case 'pdf':
            return 'pdf';
        case 'doc':
        case 'docx':
            return 'document';
        case 'sb3':
            return 'scratch';
        default:
            return 'unknown';
    }
}

function addAttachment(url) {
    const attachmentsDiv = document.getElementById('attachments');
    const filename = url.split('/').pop(); 

    const fileType = getTypeFromExtension(filename);
    console.log(filename)
    switch (fileType) {
        case 'image':
            console.log("image")
            const img = document.createElement('img');
            img.src = url;
            img.width = 200;
            attachmentsDiv.appendChild(img);
            break;
        case 'pdf':
            console.log("pdf")
            const embed = document.createElement('embed');
            embed.src = url;
            attachmentsDiv.appendChild(embed);
            break;
        case 'document':
            console.log("document")
            const iframeDoc = document.createElement('iframe');
            iframeDoc.src = url;
            attachmentsDiv.appendChild(iframeDoc);
            break;
        case 'scratch':
            console.log("scratch")
            const iframeScratch = document.createElement('iframe');
            iframeScratch.src = `https://turbowarp.org/embed?project_url=${encodeURIComponent(url)}?cloud_host=wss://cloud-data.linux-scratcher.fr`;
            iframeScratch.width = "482";
            iframeScratch.height = "412";
            iframeScratch.allowtransparency = "true";
            iframeScratch.frameborder = "0";
            iframeScratch.scrolling = "no";
            iframeScratch.allowfullscreen = true;
            attachmentsDiv.appendChild(iframeScratch);
            break;
        default:
            console.log("unknown file type");
            const message = document.createTextNode('Unsupported file type.');
            attachmentsDiv.appendChild(message);
            break;
    }
}
