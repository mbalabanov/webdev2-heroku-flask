function change_coin(){

    var coinExchangeRate = document.getElementById('selectedCoinExchangeRate');
    var selector = document.getElementById('coinSelector');
    var selectedValue = selector.options[selector.selectedIndex].value;

    console.log(selector);
    console.log(selectedValue);
    var url = 'https://min-api.cryptocompare.com/data/price?fsym='+selectedValue+'&tsyms=EUR';
    console.log(url);

    fetch(url)
        .then((resp) => resp.json())
            .then(function(response){
                coinExchangeRate.innerHTML = +response["EUR"];
    });
}
