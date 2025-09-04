let socket;
let irc;
let reconnectInterval = 2000; // Time in milliseconds (2 seconds)

// Default values
let defaultAddress = 'ws://localhost';
let defaultPort = '21213';
let defaultEndpoint = '/';

document.addEventListener('DOMContentLoaded', () => {
    // Load saved Twitch details from local storage
    document.getElementById('twitchOAuth').value = localStorage.getItem('twitchOAuth') || '';
    document.getElementById('twitchUsername').value = localStorage.getItem('twitchUsername') || '';
    document.getElementById('twitchChannel').value = localStorage.getItem('twitchChannel') || '';

    const twitchOAuth = document.getElementById('twitchOAuth');
    const twitchUsername = document.getElementById('twitchUsername');
    const twitchChannel = document.getElementById('twitchChannel');
    const saveBtn = document.getElementById('saveBtn');
    const twitchConnectBtn = document.getElementById('twitchConnectBtn');

    // Set initial state based on saved data
    updateTwitchFieldsState();

    // Auto-fill channel as user types username
    twitchUsername.addEventListener('input', () => {
        twitchChannel.value = twitchUsername.value;
    });

    // Save/Edit button functionality
    saveBtn.addEventListener('click', () => {
        if (saveBtn.textContent === 'Save') {
            // Save mode
            localStorage.setItem('twitchOAuth', twitchOAuth.value);
            localStorage.setItem('twitchUsername', twitchUsername.value);
            localStorage.setItem('twitchChannel', twitchChannel.value);
            
            // Disable fields and change to Edit mode
            twitchOAuth.disabled = true;
            twitchUsername.disabled = true;
            twitchChannel.disabled = true;
            saveBtn.textContent = 'Edit';
            twitchConnectBtn.disabled = false;
            
            updateTwitchStatus(false, 'Disconnected', 'Settings saved');
        } else {
            // Edit mode - disconnect first
            disconnectFromTwitch();
            
            // Enable fields and change to Save mode
            twitchOAuth.disabled = false;
            twitchUsername.disabled = false;
            twitchChannel.disabled = false;
            saveBtn.textContent = 'Save';
            twitchConnectBtn.disabled = true;
            
            updateTwitchStatus(false, 'Disconnected', 'Ready to edit');
        }
    });

    // Connect/Disconnect button functionality
    twitchConnectBtn.addEventListener('click', async () => {
        if (twitchConnectBtn.textContent === 'Connect') {
            await connectToTwitch();
        } else {
            disconnectFromTwitch();
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


});

// Helper function to update field states based on saved data
function updateTwitchFieldsState() {
    const hasData = localStorage.getItem('twitchOAuth') && localStorage.getItem('twitchUsername');
    const twitchOAuth = document.getElementById('twitchOAuth');
    const twitchUsername = document.getElementById('twitchUsername');
    const twitchChannel = document.getElementById('twitchChannel');
    const saveBtn = document.getElementById('saveBtn');
    const twitchConnectBtn = document.getElementById('twitchConnectBtn');
    
    if (hasData) {
        // Disable fields, show Edit button, enable Connect
        twitchOAuth.disabled = true;
        twitchUsername.disabled = true;
        twitchChannel.disabled = true;
        saveBtn.textContent = 'Edit';
        twitchConnectBtn.disabled = false;
        updateTwitchStatus(false, 'Disconnected', 'Ready to connect');
    } else {
        // Enable fields, show Save button, disable Connect
        twitchOAuth.disabled = false;
        twitchUsername.disabled = false;
        twitchChannel.disabled = false;
        saveBtn.textContent = 'Save';
        twitchConnectBtn.disabled = true;
        updateTwitchStatus(false, 'Disconnected', 'Enter credentials');
    }
}

// Updated status function with detailed reasons and button text
function updateTwitchStatus(isConnected, statusText, reason = '') {
    const statusIcon = document.getElementById('twitchStatusIcon');
    const statusTextEl = document.getElementById('twitchStatusText');
    const statusReason = document.getElementById('twitchStatusReason');
    const twitchConnectBtn = document.getElementById('twitchConnectBtn');

    if (isConnected) {
        statusIcon.textContent = '✅';
        statusTextEl.textContent = statusText || 'Connected';
        statusTextEl.classList.remove('disconnected');
        statusTextEl.classList.add('connected');
        twitchConnectBtn.textContent = 'Disconnect';
    } else {
        statusIcon.textContent = '❌';
        statusTextEl.textContent = statusText || 'Disconnected';
        statusTextEl.classList.remove('connected');
        statusTextEl.classList.add('disconnected');
        twitchConnectBtn.textContent = 'Connect';
    }
    
    statusReason.textContent = reason;
}

// Function to validate Twitch credentials using Twitch API
async function validateTwitchCredentials(oauthToken, username, channel) {
    // Clean up the OAuth token (remove 'oauth:' prefix if present)
    const cleanToken = oauthToken.replace(/^oauth:/, '');
    
    try {
        // First, validate the token and get the authenticated user
        const userResponse = await fetch('https://api.twitch.tv/helix/users', {
            headers: {
                'Authorization': `Bearer ${cleanToken}`,
                'Client-Id': 'gp762nuuoqcoxypju8c569th9wz7q5' // Using your client ID
            }
        });

        if (!userResponse.ok) {
            if (userResponse.status === 401) {
                updateTwitchStatus(false, 'Failed', 'OAuth token invalid or expired');
            } else if (userResponse.status === 403) {
                updateTwitchStatus(false, 'Failed', 'OAuth token missing required scopes');
            } else {
                updateTwitchStatus(false, 'Failed', `API error: ${userResponse.status}`);
            }
            return false;
        }

        const userData = await userResponse.json();
        const authenticatedUser = userData.data[0];

        // Check if the provided username matches the authenticated user
        if (authenticatedUser.login.toLowerCase() !== username.toLowerCase()) {
            updateTwitchStatus(false, 'Failed', `Username mismatch: token belongs to '${authenticatedUser.login}'`);
            return false;
        }

        // Now check if the target channel exists
        const channelResponse = await fetch(`https://api.twitch.tv/helix/users?login=${encodeURIComponent(channel)}`, {
            headers: {
                'Authorization': `Bearer ${cleanToken}`,
                'Client-Id': 'gp762nuuoqcoxypju8c569th9wz7q5'
            }
        });

        if (!channelResponse.ok) {
            updateTwitchStatus(false, 'Failed', 'Failed to validate channel');
            return false;
        }

        const channelData = await channelResponse.json();
        if (channelData.data.length === 0) {
            updateTwitchStatus(false, 'Failed', `Channel '${channel}' does not exist`);
            return false;
        }

        // All validations passed
        updateTwitchStatus(false, 'Validated', 'Credentials valid, connecting...');
        return true;

    } catch (error) {
        console.error('Validation error:', error);
        updateTwitchStatus(false, 'Failed', 'Network error during validation');
        return false;
    }
}

// Function to disconnect from Twitch
function disconnectFromTwitch() {
    if (irc) {
        irc.close();
        irc = null;
    }
    updateTwitchStatus(false, 'Disconnected', 'Manually disconnected');
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
        // Auto-reconnect to WebSocket
        setTimeout(() => {
            const address = document.getElementById('wsAddress').value || defaultAddress;
            const port = document.getElementById('wsPort').value || defaultPort;
            const endpoint = document.getElementById('wsEndpoint').value || defaultEndpoint;
            const wsUrl = `${address}:${port}${endpoint}`;
            socket = new WebSocket(wsUrl);
            setupWebSocket(socket);
        }, reconnectInterval);
    };

    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateStatus(false, 'statusIcon', 'statusText');
    };
}

async function connectToTwitch() {
    const oauthToken = document.getElementById('twitchOAuth').value;
    const username = document.getElementById('twitchUsername').value;
    const channel = document.getElementById('twitchChannel').value;

    if (!oauthToken || !username || !channel) {
        updateTwitchStatus(false, 'Disconnected', 'Missing credentials');
        return;
    }

    if (irc) {
        irc.close();
    }

    updateTwitchStatus(false, 'Validating', 'Checking credentials...');

    // First validate the OAuth token and username
    try {
        const isValid = await validateTwitchCredentials(oauthToken, username, channel);
        if (!isValid) {
            return; // Error already shown in validateTwitchCredentials
        }
    } catch (error) {
        updateTwitchStatus(false, 'Failed', 'Validation failed - check internet connection');
        return;
    }

    updateTwitchStatus(false, 'Connecting', 'Establishing connection...');

    irc = new WebSocket('wss://irc-ws.chat.twitch.tv:443');
    let authenticationStage = 'connecting';

    irc.onopen = () => {
        authenticationStage = 'authenticating';
        updateTwitchStatus(false, 'Authenticating', 'Sending credentials...');
        
        // Ensure OAuth token has proper format for IRC (needs oauth: prefix)
        const ircToken = oauthToken.startsWith('oauth:') ? oauthToken : `oauth:${oauthToken}`;
        
        irc.send(`PASS ${ircToken}`);
        irc.send(`NICK ${username}`);
        irc.send(`JOIN #${channel}`);
    };

    irc.onmessage = (event) => {
        console.log('Message from Twitch:', event.data);
        const message = event.data.trim();
        
        // Check for authentication success/failure
        if (message.includes('Welcome, GLHF!')) {
            updateTwitchStatus(true, 'Connected', 'Successfully connected to chat');
        } else if (message.includes('Login authentication failed')) {
            updateTwitchStatus(false, 'Failed', 'OAuth token invalid or expired');
            irc.close();
        } else if (message.includes('Invalid NICK')) {
            updateTwitchStatus(false, 'Failed', 'Username not found or invalid');
            irc.close();
        } else if (message.includes('JOIN') && message.includes(channel)) {
            updateTwitchStatus(true, 'Connected', `Joined #${channel} successfully`);
        }
    };

    irc.onclose = () => {
        console.log('Disconnected from Twitch');
        if (authenticationStage === 'connecting') {
            updateTwitchStatus(false, 'Failed', 'Connection failed - check internet');
        } else if (authenticationStage === 'authenticating') {
            updateTwitchStatus(false, 'Failed', 'Authentication timeout');
        } else {
            updateTwitchStatus(false, 'Disconnected', 'Connection closed');
        }
    };

    irc.onerror = (error) => {
        console.error('Twitch IRC error:', error);
        updateTwitchStatus(false, 'Failed', 'Connection error occurred');
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
