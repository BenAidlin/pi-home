video_stream_iframe_html = """
    <div style="margin-top: 20px; text-align:center;">
        <h2>Live Camera Stream</h2>
        <button
            id="showStreamButton"
            style="padding: 10px 20px; font-size: 16px; cursor: pointer; margin-right: 10px;">
            Show Video Stream
        </button>
        <div id="streamContainer" style="margin-top: 20px;"></div>
        <script>
            document.getElementById('showStreamButton').addEventListener('click', function() {
                const btn = this;
                const container = document.getElementById('streamContainer');

                btn.disabled = true;  // Disable the button
                btn.style.cursor = 'not-allowed';
                btn.textContent = 'Loading...';

                container.innerHTML = ''; // Clear the container first

                // Dynamically create a new iframe
                const iframe = document.createElement('iframe');
                iframe.width = "640";
                iframe.height = "480";
                iframe.src = "/video-stream/";
                iframe.frameBorder = "0";
                iframe.allowFullscreen = true;

                // When iframe loads, update the button text
                iframe.onload = function() {
                    btn.textContent = 'Stream Loaded';
                };

                // Append the new iframe to the container
                container.appendChild(iframe);
            });
        </script>
    </div>
"""
