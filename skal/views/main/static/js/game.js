
    var alphabet;
    var full_alphabet = genCharArray('a', 'z');
    var scoreDisplay = $("#score");
    var errors = $("#errors");
    var drunkDescription = $('#drunkDescription');
    var timer = $('#timer');
    var alpha = $("#alpha-display");
    var easyAudio = $("#easyAudio")[0];
    var intenseAudio = $("#intenseAudio")[0];
    var muteButton = $("#mute-button");
    var unmuteButton = $("#unmute-button");
    var startbutton = $("#start-button");
    var closeButton = $("#close-modal-button");
    var info = $("#info-container");
    var newRecord = $("#new-record");
    var HSDisplay = $("#high-score-display");
    var startTime = 0;
    var lastTime = 0;
    var errorCount = 0;
    var gameScore = 0;
    var timeRunning = false;
    var gameRunning = false;
    var gameString = "";
    var currentPlace = 1;
    var game;
    var firstClick;
    var muted;
    var drunkList = [
    "You are not even drunk, stop cheating!",
    "Oh wow, Mr. Healthy Body over here, never drinks beer and probably does cross-fit.",
    "One beer, that´s all?! Step it up",
    "I have seen a preschooler drunker than you",
    "You could use a beer, the Lager gods are getting angry",
    "You can see clearly now the beer has gone",
    "You´re not as think as you drunk you are",
    "You are drinking like a big boy now",
    "Two beer or not two beers, you have at least had seven!",
    "Seeing double? You are making your mother proud!",
    "Your blood is literally 13% alcohol",
    "BEER YOUR ASS",
    "You are getting quite drunk sir, should I ring Jeeves to fetch a car?",
    "Please stop drinking, little Timmy needs money for surgery.",
    "Things are out of control, you are drunk like grandpa AGAIN!",
    "STOP in the name of lov... IPA",
    "I would be surprised if you remember your name.",
    "I am an app and I am ashamed of you, get some help",
    "Call your ex and tell her you´ve changed, you know it´s a good idea.",
    "That´s it, Im cutting you off. GO HOME",
    "You are something beyond drunk, go home!"]

$(document).ready(function() {
    easyAudio.loop = true;
    intenseAudio.loop = true;
    firstClick=true;
    muted=false;
    unmuteButton.hide();
    info.hide();
});

$(document).click(function() {
    if(muted){
        muteButton.hide()
        unmuteButton.show()
    }else{
        unmuteButton.hide()
        muteButton.show()
    }
  
});

startbutton.click(function() {
    restartGame(true);
    if(firstClick && !muted){
      easyAudio.play();
      firstClick=false;
    }
    startbutton.hide();
    info.show();
});

$('#gameOverModal').on('hidden.bs.modal', function (e) {
  restartGame(true);
});

$('#gameOverModal').on('show.bs.modal', function(e) {
  if(high_score >= gameScore || is_anonymous){
    newRecord.hide();
  }
  else{
    high_score = gameScore;
    HSDisplay.text(gameScore)
  }
  $('#game_score_display').text(gameScore);
  $('#description_modal_display').text(findDescription());
});

function updateDescription(sec) {
  if(sec < 1){
      drunkDescription.text("We are assessing your situation darling.");
  }
  else{
      var millis = new Date().getTime() - startTime;
      var seconds = Math.round(millis / 1000);
      var scalar = (full_alphabet.length - alphabet.length-1) / full_alphabet.length;
      var score = (seconds + errorCount*4)/scalar;
      drunkDescription.text(findDescription());
  }

}

function setButtons(string){
  $( "#btn-content" ).empty();
  for(i = 1; i <=string.length; i++) {
      var btn = $('<button/>', {
          text: string[i-1], //set text 1 to 10
          id: 'btn_'+string[i-1],
          class:'col btn btn-warning border',
          onclick: "handleButtonPress('"+string[i-1]+"')"
      });
      $("#btn-content").append(btn);
      if(i%5 == 0){
          var btn_seperator = $('<div/>', {
          class:'w-100',
      });
      $("#btn-content").append(btn_seperator);
      }
  }
}

function setUI(){
    var n = full_alphabet.length - alphabet.length 
    
    var currentPlace = full_alphabet.slice(0, n);
    alpha.text(currentPlace.join(""))
    errors.text(errorCount)
}

function round(num) {    
  return +(Math.round(num + "e+2")  + "e-2");
}

function formatTime(time){
    new_time = String(Math.round(time))
    if(new_time.length == 1){
        new_time = '0'+new_time
    }
    return new_time
}

var runGame = function() {
    var millis = new Date().getTime() - startTime;
    var mill = millis/10;
    var seconds = Math.round(millis / 1000);
    var minutes = seconds / 60;
    seconds = seconds % 60;
    mill = mill % 100;
    updateDescription(seconds);
    timer.text(`${formatTime(minutes)}:${formatTime(seconds)}:${formatTime(mill)}`);
};


function handleButtonPress(char){
    if (!gameRunning) {
        startTime = new Date().getTime();
        lastTime = new Date().getTime();
        game = setInterval(runGame, 100)
        timeRunning = true;
        gameRunning = true;
        toggleMusic(false);
    }
    if(gameRunning){
        if(char == alphabet[0]){
            setScore(true)
            alphabet.shift()
            if(alphabet.length==0){
                gameOver();
                setButtons(shuffleArray(''))
            }
            else{
                var shuffle = alphabet.slice();
                setButtons(shuffleArray(shuffle))
            }
        }
        else{
            // Vibrate for 500 milliseconds
            window.navigator.vibrate(400);
            errorCount++;
            var shuffle = alphabet.slice();
            setButtons(shuffleArray(shuffle))
            setScore(false)
        }
      }
      setUI()
}

function getScoreEstimate(){
    return gameScore / Math.max(1/full_alphabet.length,Math.min(1,((full_alphabet.length-alphabet.length)/full_alphabet.length)))

}

function setScore(isCorrect){
    if(isCorrect){
        var millis = new Date().getTime() - lastTime;
        var seconds = Math.round(millis / 200);
        var score = Math.max(50 - seconds, 1);
        //var score = Math.max(100 - seconds, 0.1);
        //var new_score = (41-Math.min(log_base(score),40))
        gameScore += score;
        lastTime = new Date().getTime();
        scoreDisplay.text(gameScore);
        errors.css({ 'color': 'black', 'font-size': '100%' });
    } else{
        gameScore = Math.max(gameScore-50, 0);
        scoreDisplay.text(gameScore);
        errors.css({ 'color': 'red', 'font-size': '200%' });
    }
    
}


function log10(val) {
  return Math.log(val) / Math.log(10);
}


function shuffleArray(a){
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}


function genCharArray(charA, charZ) {
    var a = [], i = charA.charCodeAt(0), j = charZ.charCodeAt(0);
    for (; i <= j; ++i) {
        a.push(String.fromCharCode(i).toUpperCase());
    }
    return a;
}

function restartGame(first=false){
    alphabet = genCharArray('a', 'z');
    setButtons(alphabet);
    setUI()
    if(!first){
        toggleMusic(true);
    }
    drunkDescription.text("");
    gameScore=0;
    scoreDisplay.text(gameScore);
    timer.text("0");
    startTime = 0;
    timeRunning = false;
    gameRunning = false;
    errorCount = 0;
    clearInterval(game)
    errors.css({ 'color': 'black', 'font-size': '100%' });

}

function getScore(){
  var millis = new Date().getTime() - startTime;
  var seconds = Math.round(millis / 1000);
  var scalar = (full_alphabet.length-alphabet.length) / full_alphabet.length;
  var score = (seconds + errorCount*4)/scalar;
  return score
}

function findDescription() {
  var score = getScore()
  if(score < 30){
    return drunkList[0];
  }
  for(var i = 0; i < drunkList.length-1; i++){
    if(score < 30 + (i*5)){
        return drunkList[i];
    }
  }
  return drunkList[drunkList.length-1];
}

function gameOver() {
    toggleMusic(true);
    timeRunning = false;
    gameRunning = false;
    clearInterval(game)
    drunkDescription.text(findDescription());
    $('#gameOverModal').modal('show')
    sendToDatabase();
}

function sendToDatabase() {
    var xhr = new XMLHttpRequest();
    xhr.onload = function(e) {
        if(this.readyState === XMLHttpRequest.DONE) {
            if(xhr.status == '200'){
                scoreDisplay.text(gameScore)
            } else{
                promptError("Villa koma upp:", xhr.responseText, "");
            }
        }
    }
    let formData = new FormData();
    formData.append("score", gameScore);
    xhr.open("POST", post_action, true);
    xhr.send(formData);
}

function toggleMusic(normal){

  if(!normal && !muted){
      easyAudio.pause();
      intenseAudio.play();
  }
  else if(normal && !muted){
      intenseAudio.pause();
      easyAudio.play();
  }
}

function muteAudio() {
    muted = true;
    easyAudio.pause();
    intenseAudio.pause();
}

function unmuteAudio() {
    muted = false;
    if(gameRunning){
      intenseAudio.play()
    }
    else{
      easyAudio.play()
    }
}