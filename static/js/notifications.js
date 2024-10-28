
function showNotification(message, isSuccess = true) {
  const notification = document.getElementById("notification");
  notification.textContent = message;
  notification.className = `notification ${isSuccess ? "success" : "error"}`;
  notification.style.display = "block";

  // Ocultar la notificación después de 5 segundos
  setTimeout(() => {
    notification.style.display = "none";
  }, 5000);
}

document.getElementById("registroForm").addEventListener("submit", async function (event) {
  event.preventDefault();
  const formData = new FormData(this);
  const data = Object.fromEntries(formData.entries());

  try {
    const response = await fetch("/insertar-datos", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();
    if (response.ok) {
      showNotification(result.message, true);
    } else {
      showNotification(result.error, false);
    }
  } catch (error) {
    console.error("Error al enviar datos:", error);
    showNotification("Error al enviar datos", false);
  }
});
