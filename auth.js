async function handleSubmit(endpoint, formData) {
    try {
        if (!formData || Object.values(formData).some(value => value.trim() === "")) {
            alert("Preencha todos os campos antes de continuar.");
            return;
        }

        const response = await fetch(`http://localhost:5000/${endpoint}`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + (localStorage.getItem("session_token") || "")
            },
            credentials: "include",
            body: JSON.stringify(formData)
        });

        let data = {};
        try {
            data = await response.json();
        } catch (jsonError) {
            console.error('Erro inesperado no servidor:', jsonError);
            data.error = "Erro ao processar resposta do servidor";
        }

        console.log("🔹 Resposta do servidor:", data);
        
        if (!response.ok) {
            alert(data.error || "Erro ao processar requisição");
            return;
        }

        if (data.message) {
            console.log("✅ Sucesso:", data.message);
            alert(data.message);
        }

        if (data.redirect) {
            console.log("🔀 Redirecionando para:", data.redirect);
            window.location.href = data.redirect;
            return;
        }
    } catch (error) {
        console.error("❌ Erro:", error.message);
        alert("Erro ao processar requisição: " + error.message);
        return;
    }
}

// 🔥 VERIFICA SE OS ELEMENTOS EXISTEM ANTES DE ADICIONAR EVENT LISTENERS
document.addEventListener("DOMContentLoaded", function () {
    console.log("🔵 Script carregado!");

    const loginForm = document.querySelector('.sign-in form');
    const registerForm = document.querySelector('.sign-up form');
    const logoutButton = document.querySelector('.back-button');
    const saveChangesButton = document.getElementById("saveChanges");

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = e.target.querySelector('input[type="email"]').value.trim();
            const senha = e.target.querySelector('input[type="password"]').value.trim();
            await handleSubmit('login', { email, senha });
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nome = e.target.querySelector('input[type="text"]').value.trim();
            const email = e.target.querySelector('input[type="email"]').value.trim();
            const senha = e.target.querySelector('input[type="password"]').value.trim();
            const confirmSenha = e.target.querySelectorAll('input[type="password"]')[1].value.trim();
            if (senha !== confirmSenha) {
                alert('As senhas não coincidem');
                return;
            }
            await handleSubmit('register', { nome, email, senha });
        });
    }

    if (logoutButton) {
        logoutButton.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch("/logout", {
                    method: "POST",
                    credentials: "include"
                });
                if (response.ok) {
                    alert("Logout efetuado com sucesso!");
                    window.location.href = "/login.html";
                } else {
                    alert("Erro ao fazer logout");
                }
            } catch (error) {
                console.error("❌ Erro ao fazer logout:", error);
                alert("Erro ao processar logout");
            }
        });
    }

    if (saveChangesButton) {
        saveChangesButton.addEventListener("click", async () => {
            const nome = document.getElementById("name").value.trim();
            const email = document.getElementById("email").value.trim();
            const senha = document.getElementById("password").value.trim();
            const formData = { nome, email };
            if (senha) {
                formData.senha = senha;
            }
            await handleSubmit("update_user", formData);
        });
    }
});