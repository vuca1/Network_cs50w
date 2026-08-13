document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', event => {
        
        // get clicked element
        const element = event.target;

        // if clicked element is 'Edit' button
        if (element.classList.contains('edit-button')) {

            // find each related HTML elements
            const post_id = element.dataset.postId;
            const post_content = document.querySelector(`#post-content-${post_id}`);
            const text_area = document.querySelector(`#text-area-${post_id}`);

            if (!post_content.hidden) {
                // EDIT mode
                post_content.hidden = true;
                text_area.hidden = false;
                element.textContent = 'Save';
            } else {
                // SAVE mode
                // send textarea to django's view
                const url = `/edit_post/${post_id}`;
                const csrfToken = document.querySelector('meta[name="csrf_token"]').content;
                
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        content: text_area.value
                    })
                })
                .then(response => response.json())
                .then(result => {
                    
                    // check if edit was successful on server-side
                    if (result.success) {
                        // change post content
                        post_content.textContent = text_area.value;

                        // change to EDIT mode
                        post_content.hidden = false;
                        text_area.hidden = true;
                        element.textContent = 'Edit';
                    } else {
                        // Save failed
                        console.log("Could not edit post.")
                    }

                });
            }
        } else if (element.classList.contains('like-button')) {
            // like and dislike function
            const post_id = element.dataset.postId;
            const url = `/like/${post_id}`
            const csrfToken = document.querySelector('meta[name="csrf_token"]').content;
            var like = true;

            // like or dislike
            if (element.classList.contains('like')) {
                like = true;
            } else if (element.classList.contains('dislike')) {
                like = false
            }

            fetch(url, {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    like: like
                })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    document.querySelector(`#likes-count-${post_id}`).textContent = result.likes;

                    // like emojis
                    const pressed = "&#127832"
                    const not_pressed = "&#127833"

                    document.querySelector(`#like-button-${post_id}`).innerHTML = (result.liked) ? pressed : not_pressed;
                    document.querySelector(`#dislike-button-${post_id}`).innerHTML = (result.disliked) ? pressed : not_pressed;
                } else {
                    console.log("Could not edit likes or dislikes.")
                }
            });
        }
    });
});
