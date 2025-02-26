document.addEventListener("DOMContentLoaded", async function() {
    const container = document.getElementById("quartos-container");
    const totalQuartos = document.getElementById("total-quartos");

    try {
        const response = await fetch("http://localhost:5000/quartos");
        const quartos = await response.json();

        if (!response.ok) {
            throw new Error(quartos.error || "Erro ao buscar quartos.");
        }

        totalQuartos.textContent = `${quartos.length} Opções`;
        container.innerHTML = "";

        quartos.forEach(quarto => {
            const quartoDiv = document.createElement("div");
            quartoDiv.classList.add("house");
            quartoDiv.innerHTML = `
                <div class="house-img">
                    <a href="details.html?id=${quarto.id}">
                        <img src="${quarto.imagem}" alt="${quarto.nome}">
                    </a>
                </div>
                <div class="house-info">
                    <p>${quarto.tipo.toUpperCase()}</p>
                    <h2>${quarto.nome}</h2>
                    <p>${quarto.descricao}</p>
                    <div class="house-price">
                        <p>${quarto.status === 'disponivel' ? 'Disponível' : 'Indisponível'}</p>
                        <h4>${quarto.preco_noite} € <span> / Noite </span></h4>
                    </div>
                </div>
            `;
            container.appendChild(quartoDiv);
        });
    } catch (error) {
        console.error("Erro:", error);
        container.innerHTML = "<p>Erro ao carregar quartos.</p>";
    }
});
