/*!
* Start Bootstrap - Shop Homepage v5.0.6 (https://startbootstrap.com/template/shop-homepage)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-shop-homepage/blob/master/LICENSE)
*/
// This file is intentionally blank
// Use this file to add JavaScript to your project



function addToCart(productId, quantity) {
    $.ajax({
        type: 'POST',
        url: '/cart/add/',  // Your add to cart URL
        data: {
            product_id: productId,
            product_qty: quantity,
            csrfmiddlewaretoken: '{{ csrf_token }}',
            action: 'post'
        },
        success: function(response) {
            // Update the cart quantity badge
            $('#cart_quantity').text(response.qty);
            
            // Optional: Show a success message
            showNotification('Product added to cart!', 'success');
        },
        error: function(xhr, status, error) {
            console.error('Error adding to cart:', error);
            showNotification('Error adding to cart', 'error');
        }
    });
}

// Function to show notifications
function showNotification(message, type) {
    // You can use Bootstrap toasts or custom alert
    const alertDiv = $('<div class="alert alert-' + (type === 'success' ? 'success' : 'danger') + 
                      ' alert-dismissible fade show" role="alert">' +
                      message +
                      '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
                      '</div>');
    
    $('.container.mt-2').prepend(alertDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(function() {
        alertDiv.alert('close');
    }, 3000);
}