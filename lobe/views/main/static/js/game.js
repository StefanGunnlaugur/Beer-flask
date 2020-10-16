
    var alphabet;
    var full_alphabet = genCharArray('a', 'z');
    var scoreDisplay = $("#score");
    var errors = $("#errors");
    var drunkDescription = $('#drunkDescription');
    var timer = $('#timer');
    var results = $('#results');
    var input = $('#results');
    var alpha = $("#alpha-display");
    var startTime = 0;
    var errorCount = 0;
    var timeRunning = false;
    var gameRunning = false;
    var gameString = "";
    var currentPlace = 1;
    var game;
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
    restartGame();
    //var elem = document.getElementById("stopwatch");
    //timer = new Stopwatch(elem, {delay: 10});
});


function updateDescription(sec) {
  if(sec < 1){
      drunkDescription.text("We are assessing your situation darling.");
  }
  else{
      var millis = new Date().getTime() - startTime;
      var seconds = Math.round(millis / 1000);
      var scalar = (full_alphabet.length - alphabet.length-1) / full_alphabet.length;
      //console.log(scalar)
      var score = (seconds + errorCount*4)/scalar;
      console.log(score)
      drunkDescription.text(findDescription(score));
  }

}

function setButtons(string){
  $( "#btn-content" ).empty();
  for(i = 1; i <=string.length; i++) {
      var btn = $('<button/>', {
          text: string[i-1], //set text 1 to 10
          id: 'btn_'+string[i-1],
          class:'col btn btn-info border',
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
    alpha.text(alphabet.join(""))
    errors.text(errorCount)
}

function round(num) {    
  return +(Math.round(num + "e+2")  + "e-2");
}

function formatTime(time){
    new_time = String(Math.round(time))
    if(new_time.lenght == 1){
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
    //timerHandler.postDelayed(this, 50);
};


function handleButtonPress(char){
    if (!gameRunning) {
        input.text("...");
        results.text("");
        startTime = new Date().getTime();
        game = setInterval(runGame, 100)
        timeRunning = true;
        gameRunning = true;
        //gameStats.setVisibility(View.VISIBLE);
        //resultsContainer.setVisibility(View.GONE);
        //toggleMusic(false);
    }
    if(gameRunning){
        if(char == alphabet[0]){
            //errors.setTextColor(getResources().getColor(R.color.black));
            //errors.setTextSize(14);
            //gameString = gameString + values[id];
            //input.setText(gameString.toUpperCase());
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
            window.navigator.vibrate(200);
            errorCount++;
            //errors.setText(String.valueOf(errorCount));
            //errors.setTextColor(getResources().getColor(R.color.errorRed));
            //errors.setTextSize(40);
            var shuffle = alphabet.slice();
            setButtons(shuffleArray(shuffle))
        }
      }
      setUI()
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

function restartGame(){
    alphabet = genCharArray('a', 'c');
    setButtons(alphabet);
    setUI()
    //toggleMusic(true);
    drunkDescription.text("");
    //drunkDescription.setTextColor(getResources().getColor(R.color.textColor));
    //gameStats.setVisibility(View.GONE);
    //resultsContainer.setVisibility(View.GONE);
    timer.text("0");
    startTime = 0;
    timeRunning = false;
    gameRunning = false;
    //currentPlace = 1;
    errorCount = 0;
    //gameString = "";
    input.text("Start typing");
    clearInterval(game)
    //timerHandler.removeCallbacks(timerRunnable);
}

function findDescription(score) {
    if(score < 25){
        return drunkList[0];
    }
    for(var i = 0; i < drunkList.length-1; i++){
        if(score < 25 + (i*7)){
            return drunkList[i];
        }
    }
    return drunkList[drunkList.length-1];
}

function gameOver() {
    //createButtons(false);
    //toggleMusic(true);
    timeRunning = false;
    gameRunning = false;
    clearInterval(game)

    var millis = new Date().getTime() - startTime;
    var seconds = Math.round(millis / 1000);
    var score = seconds + errorCount*4;
    results.text("Your score is");
    scoreDisplay.text(score);
    drunkDescription.text(findDescription(score));
    //drunkDescription.setTextColor(getResources().getColor(R.color.black));
    sendToDatabase(score);

}

function sendToDatabase(score) {
    var xhr = new XMLHttpRequest();
    xhr.onload = function(e) {
        if(this.readyState === XMLHttpRequest.DONE) {
            if(xhr.status == '200'){
                //var beer_url = xhr.responseText;
                //window.onbeforeunload = null;
                //window.location = beer_url;
            } else{
                promptError("Villa koma upp:", xhr.responseText, "");
            }
        }
    }
    let formData = new FormData();
    formData.append("score", score);
    xhr.open("POST", post_action, true);
    xhr.send(formData);
}
