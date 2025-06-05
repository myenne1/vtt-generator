const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');
const FormData = require('form-data');

async function uploadMedia(filePath) {
    const form = new FormData();
    const fileStream = fs.createReadStream(filePath);
    form.append('file', fileStream, path.basename(filePath));

    try {
        const response = await fetch('http://localhost:8000/generate-vtt', {
            method: 'POST',
            body: form
        });

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }

        const dest = `${path.basename(filePath, path.extname(filePath))}.vtt`;
        const fileBuffer = await response.buffer();
        fs.writeFileSync(dest, fileBuffer);
        console.log(`VTT saved as: ${dest}`);
    } catch (err) {
        console.error('Upload failed:', err.message);
    }
}

uploadMedia('./Adventures Holmes Doyle.mp3');