// Global cart variable and functions for reusability
let cart = [];

/**
 * Saves the current cart state to localStorage.
 * This ensures cart persists across page loads.
 */
function saveCart() {
    localStorage.setItem('shoppingCart', JSON.stringify(cart));
}

/**
 * Loads the cart state from localStorage.
 * Called on page load to restore previous cart.
 */
function loadCart() {
    const savedCart = localStorage.getItem('shoppingCart');
    if (savedCart) {
        cart = JSON.parse(savedCart);
    }
}

/**
 * Updates the shopping cart display in the UI.
 * This function is now globally accessible.
 */
function updateCartDisplay() {
    const cartItemsContainer = document.getElementById('cart-items');
    const cartTotalSpan = document.getElementById('cart-total');

    if (!cartItemsContainer || !cartTotalSpan) {
        // Not on a page with a cart display, so just return
        return;
    }

    cartItemsContainer.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        cartItemsContainer.innerHTML = 'Your cart is empty.';
    } else {
        cart.forEach(item => {
            const cartItemDiv = document.createElement('div');
            cartItemDiv.className = 'cart-item';
            cartItemDiv.innerHTML = `
                <span>${item.name} x ${item.quantity}</span>
                <span>$${(item.price * item.quantity).toFixed(2)}</span>
                <button data-id="${item.id}" class="remove-from-cart-btn">Remove</button>
            `;
            cartItemsContainer.appendChild(cartItemDiv);
            total += item.price * item.quantity;
        });
    }
    cartTotalSpan.textContent = total.toFixed(2);
    attachRemoveFromCartListeners();
}

/**
 * Adds an item to the cart or increments its quantity.
 * This function is now globally accessible.
 */
function addToCart({ id, name, price, stock }) {
    id = parseInt(id);
    price = parseFloat(price);
    stock = parseInt(stock);

    const productInCart = cart.find(item => item.id === id);
    if (productInCart) {
        if (productInCart.quantity < stock) {
            productInCart.quantity++;
        } else {
            alert(`Cannot add more "${name}". Maximum stock reached.`);
            return;
        }
    } else {
        if (stock > 0) {
            cart.push({ id, name, price, quantity: 1, stock });
        } else {
            alert(`"${name}" is out of stock.`);
            return;
        }
    }
    updateCartDisplay();
    saveCart(); // <-- NEW: Save cart after adding
    alert(`"${name}" added to cart!`); // Provide immediate feedback
}

/**
 * Attaches event listeners to "Remove" buttons in the cart.
 */
function attachRemoveFromCartListeners() {
    const cartItemsContainer = document.getElementById('cart-items');
    if (!cartItemsContainer) return;

    document.querySelectorAll('.remove-from-cart-btn').forEach(button => {
        button.onclick = (event) => removeFromCart(parseInt(event.target.dataset.id));
    });
}

/**
 * Removes an item from the cart.
 */
function removeFromCart(id) {
    cart = cart.filter(item => item.id !== id);
    updateCartDisplay();
    saveCart(); // <-- NEW: Save cart after removing
}


// Main DOMContentLoaded listener for index.html and potentially other pages
document.addEventListener('DOMContentLoaded', () => {
    loadCart(); // <-- NEW: Load cart at the very start

    const productList = document.getElementById('product-list');
    const checkoutBtn = document.getElementById('checkout-btn');

    // --- Functions primarily for index.html ---

    // Function to fetch and display products
    async function fetchProducts() {
        try {
            const response = await fetch('/api/products');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const products = await response.json();
            displayProducts(products);
        } catch (error) {
            console.error('Error fetching products:', error);
            if (productList) {
                productList.innerHTML = '<p>Error loading products. Please try again later.</p>';
            }
        }
    }

    // Function to display products
    function displayProducts(products) {
        if (!productList) return; // Only run if on the index page

        productList.innerHTML = ''; // Clear previous products
        if (products.length === 0) {
            productList.innerHTML = '<p>No products available at the moment.</p>';
            return;
        }
        products.forEach(product => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card';
            productCard.innerHTML = `
                <a href="/product/${product.id}"> <img src="${product.imageUrl}" alt="${product.name}">
                    <h3>${product.name}</h3>
                </a>
                <p>Stock: ${product.stock}</p>
                <p>$${product.price.toFixed(2)}</p>
                <button data-id="${product.id}" data-name="${product.name}" data-price="${product.price}" data-stock="${product.stock}">Add to Cart</button>
            `;
            productList.appendChild(productCard);
        });
        attachAddToCartButtonsToIndex(); // Attach listeners for buttons on index page
    }

    // Function to attach event listeners to "Add to Cart" buttons on index.html
    function attachAddToCartButtonsToIndex() {
        if (!productList) return; // Only run if on the index page
        document.querySelectorAll('#product-list button').forEach(button => {
            button.onclick = (event) => addToCart(event.target.dataset);
        });
    }

    // Checkout button click handler
    if (checkoutBtn) { // Only attach if checkoutBtn exists (only on index.html)
        checkoutBtn.onclick = async () => {
            if (cart.length === 0) {
                alert('Your cart is empty!');
                return;
            }

            try {
                const response = await fetch('/api/checkout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ cartItems: cart }),
                });

                if (response.status === 401) { // Unauthorized (not logged in)
                    alert('Please log in to complete your purchase.');
                    window.location.href = '/login?next=/';
                    return;
                }

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                alert(result.message);
                cart = []; // Clear cart on successful checkout
                saveCart(); // <-- NEW: Save empty cart after checkout
                updateCartDisplay(); // Update cart display
                fetchProducts(); // Re-fetch products to update stock display
            } catch (error) {
                console.error('Error during checkout:', error);
                alert('Checkout failed: ' + error.message);
            }
        };
    }

    // Initial load: Fetch products and update cart when the page is ready
    if (productList) { // Only fetch products if product-list exists (i.e., on index.html)
        fetchProducts();
    }
    updateCartDisplay(); // Always update cart display if elements exist


    // --- Order History Functions ---
    async function fetchOrderHistory() {
        const ordersListDiv = document.getElementById('orders-list');
        const noOrdersDiv = document.getElementById('no-orders');

        if (!ordersListDiv || !noOrdersDiv) {
            return;
        }

        try {
            const response = await fetch('/api/orders');
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login?next=/orders';
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const orders = await response.json();

            ordersListDiv.innerHTML = '';

            if (orders.length === 0) {
                noOrdersDiv.style.display = 'block';
                ordersListDiv.style.display = 'none';
            } else {
                noOrdersDiv.style.display = 'none';
                ordersListDiv.style.display = 'block';

                orders.forEach(order => {
                    const orderDiv = document.createElement('div');
                    orderDiv.className = 'order-card';

                    let itemsHtml = order.items.map(item => `
                        <li>${item.product_name} x ${item.quantity} - $${item.price_at_purchase.toFixed(2)} each</li>
                    `).join('');

                    orderDiv.innerHTML = `
                        <h3>Order ID: ${order.order_id}</h3>
                        <p><strong>Order Date:</strong> ${order.order_date}</p>
                        <p><strong>Total Amount:</strong> $${order.total_amount.toFixed(2)}</p>
                        <h4>Items:</h4>
                        <ul>
                            ${itemsHtml}
                        </ul>
                    `;
                    ordersListDiv.appendChild(orderDiv);
                });
            }

        } catch (error) {
            console.error('Error fetching order history:', error);
            ordersListDiv.innerHTML = '<p style="color: red;">Failed to load order history. Please try again later.</p>';
            noOrdersDiv.style.display = 'none';
        }
    }

    // Call fetchOrderHistory when the DOM is loaded, but only if on the orders page
    if (document.getElementById('order-history')) {
        fetchOrderHistory();
    }


    // --- Product Detail Page Specific Logic ---
    const productDetailAddToCartBtn = document.querySelector('.product-detail-info .add-to-cart-btn');
    if (productDetailAddToCartBtn) {
        productDetailAddToCartBtn.addEventListener('click', (event) => {
            const { id, name, price, stock } = event.target.dataset;
            addToCart({ id: parseInt(id), name, price: parseFloat(price), stock: parseInt(stock) });
        });
    }
});