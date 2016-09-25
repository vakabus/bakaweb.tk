Array.prototype.contains = function(x) {
	for (i = 0; i < this.length;i++) {
		if (this[i] == x) return true;
	}
	return false;
};


function checkLibraries() {
	// Check for the various File API support.
	if (window.File && window.FileReader && window.FileList && window.Blob) {
		console.log("Knihovny v prohlížeči jsou v pořádku...")
		// Great success! All the File APIs are supported.
	} else {
		alert('The File APIs are not fully supported in this browser.');
	}
	if(typeof(Storage) !== "undefined") {
	} else {
		alert("Web storage is not supported in this browser. Progress won't be saved.")
	}
}


function Question(que,ans,img) {
	this.question = (que == undefined ? '' : que);
	this.answer = (ans == undefined ? '' : ans.toUpperCase());
	this.image = (img == undefined ? '' : img);
}


function Test() {
	this.topic = '';
	this.description = '';
	this.questions = []

	this.questionBuffer = [];

	this.selected = -1;
	this.wrong = 0;
	this.right = 0;
}

/*
*	PUBLIC
*/
Test.prototype.answer = function(answer, callback) {
	this.checkAnswer(answer);
	this.selectQuestion();
	callback();
};
Test.prototype.getSelectedQuestion = function() {
	return this.questionBuffer[this.selected];
}


/*
*  INTERNALS
*/
Test.prototype.addQuestion = function(question) {
	this.questions.push(question);
};
Test.prototype.selectQuestion = function() {
	if ( this.questionBuffer.length == 0) {
		this.fillBuffer();
	}

	this.selected = Math.floor(Math.random()*(this.questionBuffer.length));
};
Test.prototype.checkAnswer = function(answer) {
	if (this.getSelectedQuestion().answer.toUpperCase().split("##").contains(answer.toUpperCase())) {
		//Spravna odpoved
		this.right++;
		this.questionBuffer.splice(this.selected,1);
	} else {
		//Spatna odpoved
		alert('Špatně - "'+this.getSelectedQuestion().answer+'"');
		this.wrong++;
	}
};
Test.prototype.removeEmptyQuestions = function() {
	for (var x = test.questions.length-1; x > -1; x--) {
		if (test.questions[x].image == '' && test.questions[x].question == '' && test.questions[x].answer == '') {
			test.questions.splice(x,1);
		}
	}
};
Test.prototype.fillBuffer = function() {
	this.questionBuffer = this.questions.slice(0);	//this is here for creating new array, not copying reference
};



/*
*	BROWSER CRASH PROTECTION
*/
Test.prototype.save = function() {
	if(typeof(Storage) !== "undefined") {
		localStorage.setItem('lastTest',JSON.stringify(this));
		console.log('saved');
	}
};
Test.prototype.load = function() {
	if(typeof(Storage) !== "undefined") {
		var old = JSON.parse(localStorage.getItem("lastTest"));
		this.selected = old.selected;
		this.topic = old.topic;
		this.description = old.description;
		this.questions = old.questions;
		this.questionBuffer = old.questionBuffer;
		this.wrong = old.wrong;
		this.right = old.right;
	};
}


/*
*   DATA EXPORTING/INPORTING
*/
Test.prototype.loadXML = function(xml) {
	var parser = new DOMParser();
	var xmlDoc = parser.parseFromString(xml,"text/xml");
	this.topic = xmlDoc.getElementsByTagName('nadpis')[0].innerHTML;
	this.description = xmlDoc.getElementsByTagName('popis')[0].innerHTML;
	var ot = xmlDoc.getElementsByTagName('otazka');
	for (var i = 0; i < ot.length; i++) {
		this.addQuestion(new Question(ot[i].getAttribute('otazka'),ot[i].getAttribute('odpoved'),ot[i].getAttribute('uri_obrazku')));
	}
	this.selectQuestion();
};
Test.prototype.loadJSON = function(json) {
	var test = JSON.parse(json)

	this.topic = test.topic
	this.description = test.description
	this.questions = test.questions

	this.selectQuestion();
}
Test.prototype.generateJSON = function() {
	this.removeEmptyQuestions()

	var test = new Object();
	test.topic = this.topic
	test.description = this.description;
	test.questions = this.questions

	return JSON.stringify(test, null, 2)
}
Test.prototype.generateXML = function() {
	this.removeEmptyQuestions();
	xml = '<?xml version="1.0" encoding="UTF-8"?>\n<test>\n\t<nadpis>' + this.topic + '</nadpis>\n\t<popis>' + this.description + '</popis>\n';
	for (var q =0; q < test.questions.length; q++) {
		xml = xml + '\t<otazka otazka="' + test.questions[q].question + '" odpoved="' + test.questions[q].answer + '" uri_obrazku="' + test.questions[q].image + '" />\n';
	}
	xml = xml + "</test>"
	return xml;
}
