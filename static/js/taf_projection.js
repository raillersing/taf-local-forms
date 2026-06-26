(function() {
    function setFeedback(root, message, isError) {
        var feedback = root.querySelector("[data-copy-feedback]");
        if (!feedback) {
            return;
        }
        feedback.textContent = message;
        feedback.classList.toggle("is-error", Boolean(isError));
    }

    function renderQr(target, url) {
        if (!target || !url || typeof QRCode === "undefined") {
            return;
        }
        target.innerHTML = "";
        new QRCode(target, {
            text: url,
            width: target.dataset.qrSize || 192,
            height: target.dataset.qrSize || 192,
            correctLevel: QRCode.CorrectLevel.M,
        });
    }

    function copyText(root, text) {
        if (!text) {
            setFeedback(root, "URL LAN non configurée.", true);
            return;
        }

        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function() {
                setFeedback(root, "URL copiée.");
            }).catch(function() {
                setFeedback(root, "Copie indisponible sur ce navigateur.", true);
            });
            return;
        }

        var field = document.createElement("textarea");
        field.value = text;
        field.setAttribute("readonly", "readonly");
        field.className = "taf-visually-hidden";
        document.body.appendChild(field);
        field.select();

        try {
            document.execCommand("copy");
            setFeedback(root, "URL copiée.");
        } catch (error) {
            setFeedback(root, "Copie indisponible sur ce navigateur.", true);
        }

        document.body.removeChild(field);
    }

    function toggleFullscreen(root) {
        var fullscreenTarget = root.closest(".projection-stage") || root;
        if (!document.fullscreenEnabled || !fullscreenTarget.requestFullscreen) {
            setFeedback(root, "Plein écran indisponible sur cet appareil.", true);
            return;
        }

        if (document.fullscreenElement) {
            document.exitFullscreen();
            return;
        }

        fullscreenTarget.requestFullscreen().catch(function() {
            setFeedback(root, "Impossible d'activer le plein écran.", true);
        });
    }

    function initAccessBlock(root) {
        var url = root.dataset.studentUrl || "";
        var qrTarget = root.querySelector("[data-qr-target]");
        var copyButton = root.querySelector("[data-copy-url]");
        var fullscreenButton = root.querySelector("[data-fullscreen-toggle]");

        renderQr(qrTarget, url);

        if (copyButton) {
            copyButton.addEventListener("click", function() {
                copyText(root, url);
            });
        }

        if (fullscreenButton) {
            fullscreenButton.addEventListener("click", function() {
                toggleFullscreen(root);
            });
        }
    }

    document.addEventListener("DOMContentLoaded", function() {
        var blocks = document.querySelectorAll("[data-student-access]");
        for (var i = 0; i < blocks.length; i += 1) {
            initAccessBlock(blocks[i]);
        }
    });
})();
