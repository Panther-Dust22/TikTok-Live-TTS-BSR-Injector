let socket;
let irc;
let isTwitchEnabled = false; // Track whether Twitch is enabled
let reconnectInterval = 2000; // Time in milliseconds (10 seconds)

// Default values
let defaultAddress = 'ws://localhost';
let defaultPort = '21213';
let defaultEndpoint = '/';

document.addEventListener('DOMContentLoaded', () => {
    // Load saved Twitch details from local storage
    document.getElementById('twitchOAuth').value = localStorage.getItem('twitchOAuth') || '';
    document.getElementById('twitchUsername').value = localStorage.getItem('twitchUsername') || '';
    document.getElementById('twitchChannel').value = localStorage.getItem('twitchChannel') || '';

    const twitchToggle = document.getElementById('twitchToggle');
    const twitchOAuth = document.getElementById('twitchOAuth');
    const twitchUsername = document.getElementById('twitchUsername');
    const twitchChannel = document.getElementById('twitchChannel');
    const saveBtn = document.getElementById('saveBtn');

    // Set the initial state of the input fields based on the toggle
    isTwitchEnabled = twitchToggle.checked;
    toggleTwitchInputs(isTwitchEnabled);

    // Event listener for the Twitch toggle switch
    twitchToggle.addEventListener('change', () => {
        isTwitchEnabled = twitchToggle.checked;
        toggleTwitchInputs(isTwitchEnabled);

        if (isTwitchEnabled) {
            connectToTwitch();  // Try to connect when the switch is turned on
        } else if (irc) {
            irc.close();  // Disconnect from Twitch if it was connected
            updateStatus(false, 'twitchStatusIcon', 'twitchStatusText');
        }
    });

    saveBtn.addEventListener('click', () => {
        // Save Twitch details to local storage
        localStorage.setItem('twitchOAuth', document.getElementById('twitchOAuth').value);
        localStorage.setItem('twitchUsername', document.getElementById('twitchUsername').value);
        localStorage.setItem('twitchChannel', document.getElementById('twitchChannel').value);
        alert('Twitch details saved!');

        if (isTwitchEnabled) {
            connectToTwitch();  // Reconnect after saving details if toggle is on
        }
    });

    document.getElementById('connectBtn').addEventListener('click', () => {
        const address = document.getElementById('wsAddress').value || defaultAddress;
        const port = document.getElementById('wsPort').value || defaultPort;
        const endpoint = document.getElementById('wsEndpoint').value || defaultEndpoint;
        const wsUrl = `${address}:${port}${endpoint}`;

        if (socket) {
            socket.close();
        }

        socket = new WebSocket(wsUrl);
        setupWebSocket(socket);
    });

    // Automatically connect to Twitch on page load if toggle is on and details are available
    if (localStorage.getItem('twitchOAuth') && localStorage.getItem('twitchUsername') && localStorage.getItem('twitchChannel') && isTwitchEnabled) {
        connectToTwitch();
    }
});

function toggleTwitchInputs(isEnabled) {
    // Enable or disable Twitch inputs based on the switch
    document.getElementById('twitchOAuth').disabled = !isEnabled;
    document.getElementById('twitchUsername').disabled = !isEnabled;
    document.getElementById('twitchChannel').disabled = !isEnabled;
    document.getElementById('saveBtn').disabled = !isEnabled;
}

function setupWebSocket(socket) {
    socket.onopen = function(event) {
        console.log('WebSocket is connected.');
        updateStatus(true, 'statusIcon', 'statusText');
    };

    socket.onmessage = function(event) {
        const message = JSON.parse(event.data);

        if (message.event === 'chat') {
            const data = message.data;
            displayChatData(data);
            processAndSendToTwitch(data);
        }
    };

    socket.onclose = function(event) {
        console.log('WebSocket is closed.');
        updateStatus(false, 'statusIcon', 'statusText');
        // Try to reconnect after the specified delay if Twitch is enabled
        if (isTwitchEnabled) {
            setTimeout(() => {
                const address = document.getElementById('wsAddress').value || defaultAddress;
                const port = document.getElementById('wsPort').value || defaultPort;
                const endpoint = document.getElementById('wsEndpoint').value || defaultEndpoint;
                const wsUrl = `${address}:${port}${endpoint}`;
                socket = new WebSocket(wsUrl);
                setupWebSocket(socket);
            }, reconnectInterval);
        }
    };

    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateStatus(false, 'statusIcon', 'statusText');
    };
}

function connectToTwitch() {
    const oauthToken = document.getElementById('twitchOAuth').value;
    const username = document.getElementById('twitchUsername').value;
    const channel = document.getElementById('twitchChannel').value;

    if (!oauthToken || !username || !channel) {
        console.log("Twitch details are missing!");
        return;
    }

    if (irc) {
        irc.close();
    }

    irc = new WebSocket('wss://irc-ws.chat.twitch.tv:443');

    irc.onopen = () => {
        irc.send(`PASS oauth:${oauthToken}`);
        irc.send(`NICK ${username}`);
        irc.send(`JOIN #${channel}`);
        updateStatus(true, 'twitchStatusIcon', 'twitchStatusText');
    };

    irc.onmessage = (event) => {
        console.log('Message from Twitch:', event.data);
    };

    irc.onclose = () => {
        console.log('Disconnected from Twitch');
        updateStatus(false, 'twitchStatusIcon', 'twitchStatusText');
        // Try to reconnect after the specified delay if Twitch is enabled
        if (isTwitchEnabled) {
            setTimeout(connectToTwitch, reconnectInterval);
        }
    };

    irc.onerror = (error) => {
        console.error('Twitch IRC error:', error);
        updateStatus(false, 'twitchStatusIcon', 'twitchStatusText');
    };
}

function sendToTwitch(message) {
    if (irc && irc.readyState === WebSocket.OPEN) {
        const channel = document.getElementById('twitchChannel').value;
        irc.send(`PRIVMSG #${channel} :${message}`);
        console.log(`Message sent to Twitch: ${message}`);
    } else {
        console.log('Twitch IRC is not connected.');
    }
}

function displayChatData(data) {
    const dataBox = document.getElementById('dataBox');
    const chatMessage = `
        ${data.uniqueId}, ${data.nickname}, ${data.followRole}
        ${data.comment}
        ${data.isModerator}, ${data.isSubscriber}, ${data.topGifterRank}
    `;
    dataBox.value += chatMessage + '\n\n';
}

function updateStatus(isConnected, iconId, textId) {
    const statusIcon = document.getElementById(iconId);
    const statusText = document.getElementById(textId);

    if (isConnected) {
        statusIcon.textContent = '✅';
        statusText.textContent = 'Connected';
        statusText.classList.remove('disconnected');
        statusText.classList.add('connected');
    } else {
        statusIcon.textContent = '❌';
        statusText.textContent = 'NOPE!';
        statusText.classList.remove('connected');
        statusText.classList.add('disconnected');
    }
}

function processAndSendToTwitch(data) {
    const comment = data.comment;
    const nickname = data.nickname;
    const isModerator = data.isModerator; // Assuming this comes in as a boolean

    // Filter messages based on moderator status
    if ((comment.startsWith('!open') || comment.startsWith('!close')) && isModerator !== true) {
        console.log('Message not sent: User is not a moderator.');
        return;
    }

    let message;

    if (comment.startsWith('bsr')) {
        // Send the first message with "!" prepended to "bsr"
        message = `!${comment} - ${nickname}`;
        sendToTwitch(message);

        // Send the second message after 1 second
        setTimeout(() => {
            // Remove "bsr" from the second message
            const commentWithoutBsr = comment.replace(/^bsr\s*/, ''); // Removes "bsr" and any leading space
            const secondMessage = `!songmsg ${commentWithoutBsr} ${nickname}`;
            sendToTwitch(secondMessage);
        }, 1000); // 1-second delay
    } else {
        // Regular message
        message = `${comment} - ${nickname}`;
        sendToTwitch(message);
    }
}

// Prevent user input in the text area
document.getElementById('dataBox').addEventListener('keydown', (e) => {
    e.preventDefault();
});

// Initialize WebSocket with default settings
socket = new WebSocket(`${defaultAddress}:${defaultPort}${defaultEndpoint}`);
setupWebSocket(socket);
