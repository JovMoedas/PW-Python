// Função para obter os produtos guardados no LocalStorage
function obterCarrinho() {
    return JSON.parse(localStorage.getItem("carrinho")) || [];
}

// Função para carregar os produtos no carrinho
function carregarCarrinho() {
    let carrinho = obterCarrinho();
    let carrinhoContainer = document.getElementById("carrinho-container");
    let totalContainer = document.querySelector(".total-price");

    carrinhoContainer.innerHTML = ""; // Limpa o carrinho antes de recarregar

    if (carrinho.length === 0) {
        carrinhoContainer.innerHTML = "<p>O seu carrinho está vazio.</p>";
        totalContainer.textContent = "0,00 €";
        return;
    }

    let total = 0;

    carrinho.forEach((produto, index) => {
        let item = document.createElement("div");
        item.classList.add("cart-item");
        item.innerHTML = `
            <img src="${produto.imagem}" alt="${produto.nome}">
            <div class="cart-item-details">
                <h3>${produto.nome}</h3>
                <p>${produto.descricao}</p>
            </div>
            <div class="cart-item-price">${produto.preco.toFixed(2)} €</div>
            <button class="remover-item" onclick="removerDoCarrinho(${index})">Remover</button>
        `;
        carrinhoContainer.appendChild(item);
        total += produto.preco;
    });

    totalContainer.textContent = `${total.toFixed(2)} €`;
}

// Função para remover um item do carrinho
function removerDoCarrinho(index) {
    let carrinho = obterCarrinho();
    carrinho.splice(index, 1);
    localStorage.setItem("carrinho", JSON.stringify(carrinho));
    carregarCarrinho(); // Atualiza a interface
}

// Finalizar compra (limpa o carrinho e redireciona para checkout)
document.getElementById("finalizarCompra").addEventListener("click", function() {
    alert("Compra finalizada com sucesso!");
    localStorage.removeItem("carrinho"); // Limpa os itens do carrinho
    window.location.href = "checkout.html"; // Redireciona para checkout
});

// Chama a função para carregar os produtos ao abrir a página
document.addEventListener("DOMContentLoaded", carregarCarrinho);
