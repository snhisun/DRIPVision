// static/script.js
document.getElementById('add-stock').addEventListener('click', function() {
    var stocksDiv = document.getElementById('stocks');
    var newEntry = document.createElement('div');
    newEntry.className = 'stock-entry';
    newEntry.innerHTML = `
        <input type="text" name="ticker[]" placeholder="Stock Ticker (e.g., AAPL)" required>
        <input type="number" name="weight[]" placeholder="Weight (%)" min="0" max="100" required>
        <button type="button" class="remove-stock">Remove</button>
    `;
    stocksDiv.appendChild(newEntry);

    var removeButtons = document.getElementsByClassName('remove-stock');
    for (var i = 0; i < removeButtons.length; i++) {
        removeButtons[i].onclick = function() {
            this.parentNode.remove();
        };
    }
});
