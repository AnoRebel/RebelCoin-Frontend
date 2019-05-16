$(function() {
    // Global variable to tell if mining or not
    $miningInProgress = false;
    /*
    Binding the cards to a click function to
    AJAX to the server and set the selected block
    */
    $('.card').bind('click', function () {
        NProgress.start();
        NProgress.configure({ minimum: 0.2 });
        NProgress.inc(0.2);
        $.getJSON($BASE_URL + "_select_block", {
            block_id: $(this).data('value')
        }, function(data) {
            $('#transaction').text(data.result);
            console.log(data.result);
            location.reload();
            NProgress.done();
        });
        NProgress.done(true);
        return false;
    });
    /*
    AJAX call to change the difficulty in the server
    everytime the input changes
    */
    $('#difficulty').on('input', function () {
        NProgress.start();
        NProgress.configure({ minimum: 0.2 });
        NProgress.inc(0.2);
        $.getJSON($BASE_URL + "_set_settings", {
            difficulty: $(this).val(),
        }, function(data) {
            // $('#difficulty').val(data.difficulty);
            // console.log(data.difficulty);
            NProgress.done();
        });
        NProgress.done(true);
        return false;
    });
    /*
    AJAX call to change the mining reward in the server
    everytime the input changes
    */
    $('#miningReward').on('input', function () {
        NProgress.start();
        NProgress.configure({ minimum: 0.2 });
        NProgress.inc(0.2);
        $.getJSON($BASE_URL + "_set_settings", {
            reward: $(this).val(),
        }, function(data) {
            $('#reward').val(data.reward);
            // console.log(data.reward);
            NProgress.done();
        });
        NProgress.done(true);
        return false;
    });
    // Another AJAX call to the server to remove the intro message
    $('#showInfoMessage').on('closed.bs.alert', function () {
        $.getJSON($BASE_URL + "_dismissInfo", {
            value: "False",
        }, function (data) {
            console.info('Status: ' + data.status + '\n' + 'Message: ' + data.message);
        });
        return false;
    });
    // AJAX call to tell  the server to mine the pending transactions in the queue
    $('#minePendingTransactions').on('click', function () {
        $miningInProgress = true;
        NProgress.start();
        NProgress.configure({ minimum: 0.2 });
        NProgress.inc(0.2);
        $( this ).toggle();
        $('#miningInProgress').attr('hidden', !$miningInProgress);
        $.ajax({
            url: $BASE_URL + "_mine_transactions",
            data: { miningInProgress: $miningInProgress },
            type: 'POST',
            success: function (data) {
                console.log(data.status + '\n' + data.message);
                $miningInProgress = false;
                $('#miningInProgress').attr('hidden', !$miningInProgress);
                $('#minePendingTransactions').toggle();
                // $('#minePendingTransactions').attr('hidden', $miningInProgress);
                NProgress.done();
                location.href = location.origin;
            },
            error: function (error) {
                alert(error.responseText);
                NProgress.done(true);
            }
        });
    });
    // A little snippet to remove the added transaction alert
    setTimeout(() => {
        $('#addedTrans').alert('close');
    }, 4000);
});
