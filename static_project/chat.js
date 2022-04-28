function validateText(str){
    let md = window.markdownit({
        highlight: function (str, lang) {
        if (lang && hljs.getLanguage(lang)) {
          try {
            return '<pre class="hljs"><code>' +
                   hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
                   '</code></pre>';
          } catch (__) {}
        }

        return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
        },
        linkify: true,
        });
        return md.render(str);
}

// public chat functions
function initPublicChat(ws_path, room_id, is_auth) {
      let public_chat_socket = new WebSocket(ws_path)
      is_auth = is_auth === "True";

      public_chat_socket.onmessage = function (message) {
        console.log("Got chat websocket message: " + message.data)

        let data = JSON.parse(message.data)

        displayChatroomLoadingSpinner(data.display_progress_bar)

        if (data.error) {
          showClientErrorModal(data.message)
        }
        if (data.join) {
          getRoomChatMessages();
          showClientJoinMessage(data.username, data.profile_slug)
        }
        if (data.msg_type === 0) {
          appendChatMessage(data, false, true)
        } else if (data.msg_type === 1) {
          updateConnectedUsers(data['connected_users'])
        }

        if (data.messages_payload) {
          handleMessagesPayload(data.messages, data.new_page_number);
          if (data.new_page_number === 2) {
            let chat_container = document.getElementsByClassName('chat-messages')[0]
            chat_container.scrollTop = chat_container.scrollHeight
          }
        }

      }

      public_chat_socket.addEventListener("open", function (e) {
        console.log("Public Chat Socket OPEN")
        if (is_auth) {
          public_chat_socket.send(JSON.stringify
                  ({
                    "command": "join",
                    "room_id": room_id
                  })
          )
        }
      })

      public_chat_socket.onclose = function (e) {
        console.log("Public Chat Socket CLOSED")
        if (is_auth) {
          public_chat_socket.send(JSON.stringify
                  ({
                    "command": "leave",
                    "room_id": room_id
                  })
          )
        }
      }

      public_chat_socket.onopen = function (e) {
        console.log("Public Chat Socket: onOpen")
      }

      public_chat_socket.onerror = function (e) {
        console.log("Public Chat Socket: onError " + e)
      }

      if (public_chat_socket.readyState === WebSocket.OPEN) {
        console.log("Public Chat Socket OPEN")
      } else if (public_chat_socket.readyState === WebSocket.CONNECTING) {
        console.log("Public Chat Socket CONNECTING...")
      }
      document.getElementById("id_chat_message_input").focus()

      function sendMessageOnEnterToSocket(e) {
        if (e.keyCode === 13 && e.shiftKey) {
          document.getElementById("id_chat_message_submit").click()
        }
      }

      document.getElementById("id_chat_message_submit").addEventListener("click", sendMessageToSocket);
      document.getElementById("id_chat_message_input").addEventListener("keyup", sendMessageOnEnterToSocket);

      function sendMessageToSocket(e) {
        const messageInputDom = document.getElementById("id_chat_message_input")
        const message = messageInputDom.value
        public_chat_socket.send(JSON.stringify({
          "command": "send",
          "message": message,
          "room_id": room_id
        }))
        messageInputDom.value = ""
      }

      function displayChatroomLoadingSpinner(isDisplayed) {
        let spinner = document.getElementById('loading_spinner')
        if (isDisplayed) {
          spinner.classList.add('active');
        } else {
          spinner.classList.remove('active');
        }
      }

      function setPageNumber(pageNumber) {
        document.getElementById("chat_page_number").innerHTML = pageNumber;
      }


      // когда больше не осталось страниц либо страница в процессе загрузки
      function setPageNumLast() {
        setPageNumber("-1");
      }

      function getRoomChatMessages() {
        let pageNumber = document.getElementById("chat_page_number").innerHTML
        if (pageNumber !== "-1") {
          setPageNumLast();
          public_chat_socket.send(JSON.stringify({
            "command": "get_room_chat_messages",
            "room_id": room_id,
            "page_number": pageNumber
          }))
        }
      }

      function handleMessagesPayload(messages, new_page_number) {
        if (messages != null && messages !== "undefined" && messages !== "None") {
          setPageNumber(new_page_number)
          messages.forEach(function (message) {
            appendChatMessage(message, true, false)
          })
        } else {
          setPageNumLast()
        }
      }

      let chatContainer = document.getElementsByClassName("chat-messages")[0]
      chatContainer.addEventListener("scroll", function (e) {
        if (chatContainer.scrollTop < 30) {
          getRoomChatMessages();
        }
      })

      function appendChatMessage(data, maintainPosition, isNewMessage) {
        let profile_image = data['profile_image']
        let username = data['username']
        let user_id = data['user_id']
        let msg = data['message']
        let timestamp = data['timestamp']
        let profile_slug = data['profile_slug']
        createChatMessageElement(profile_image, username,
                user_id, msg, profile_slug, timestamp,
                maintainPosition, isNewMessage)
      }

      function createChatMessageElement(profile_image, username, user_id, msg,
                                        profile_slug, timestamp, maintainPosition, isNewMessage) {
        let chat_container = document.getElementsByClassName('chat-messages')[0]
        msg = validateText(msg)
        if (isNewMessage) {
          chat_container.innerHTML += `<div class="chat-message"> \
      <a class="chat-avatar">
        <img src="${profile_image}">
      </a>
      <div class="content">
        <a href='/profiles/${profile_slug}' class="author">${username}</a>
        <div class="metadata">
          <span class="date">${timestamp}</span>
        </div>
        <div class="text">
          ${msg}
        </div>
      </div>`;
        } else {
          let msgDiv = document.createElement('div');
          msgDiv.classList.add("chat-message");
          msgDiv.innerHTML += `<a class="chat-avatar">
        <img src="${profile_image}">
      </a>
      <div class="content">
        <a href='/profiles/${profile_slug}' class="author">${username}</a>
        <div class="metadata">
          <span class="date">${timestamp}</span>
        </div>
        <div class="text">
          ${msg}
        </div>`;
          chat_container.insertBefore(msgDiv, chat_container.firstChild);
        }

        if (maintainPosition) {
          // let posScroll = chat_container.scrollTop;
          // chat_container.scrollTop =  posScroll
        } else {
          chat_container.scrollTop = chat_container.scrollHeight
        }

        // после обновления HTML сбрасываются EventListener, каждый раз вешаем заново
        document.getElementById("id_chat_message_submit").addEventListener("click", sendMessageToSocket);
        document.getElementById("id_chat_message_input").addEventListener("keyup", sendMessageOnEnterToSocket);
      }

      function showClientErrorModal(msg) {
        let chat_container = document.getElementsByClassName('chat-messages')[0]
        chat_container.innerHTML += `<div class="chat-message chat-info"> \
      <a class="chat-avatar">
        <i class="info circle icon chat-info-icon-red"></i>
      </a>
      <div class="content">
        <a href='#' class="author">Error</a>
        <div class="metadata">
          <span class="date">just now</span>
        </div>
        <div class="text">
          ${msg}
        </div>
      </div>`;
        chat_container.scrollTop = chat_container.scrollHeight

        // скрытие ошибки через 2 секунды
        function fadeOut() {
          $(".chat-info").fadeToggle(500, "swing", function () {
            this.remove();
          });
        }

        let delay = 2000;
        setTimeout(fadeOut, delay);
      }

      function showClientJoinMessage(username, profile_slug) {
        // chat_container = document.getElementsByClassName('chat-messages')[0]
        // chat_container.innerHTML += `<div class="chat-message chat-info"> \
        // <a class="chat-avatar">
        //   <i class="comment alternate icon chat-info-icon-black"></i>
        // </a>
        // <div class="content">
        //   <a href='/profiles/${profile_slug}' class="author">Chat info</a>
        //   <div class="metadata">
        //     <span class="date"><p><a href="/profiles/${profile_slug}">${username}</a> joined to chat</p></span>
        //   </div>
        //   <div class="text">
        //
        //   </div>
        // </div>`;
        // chat_container.scrollTop = chat_container.scrollHeight
      }

      function updateConnectedUsers(users) {
        let users_container = document.getElementsByClassName('users-in-room-cards')[0]
        let users_in_room = document.getElementsByClassName('black card');
        while (users_in_room.length) {
          users_in_room[0].parentNode.removeChild(users_in_room[0]);
        }
        let usersCounter = 0;
        for (let user in users) {
          let user_card = document.createElement('a');
          user_card.classList.add('black', 'card');
          let user_href = 'profiles/' + users[user]['profile_slug'];
          user_card.setAttribute("href", user_href);
          user_card.innerHTML += `
        <div class="image">
          <img src="${users[user]['profile_image']}" alt="avatar">
            <p>${users[user]['username']}</p>
        </div>`
          users_container.appendChild(user_card)
          usersCounter++;
        }
        let usersCounterUI = document.getElementById('users-counter')
        usersCounterUI.textContent = usersCounter;
      }

    }
    
