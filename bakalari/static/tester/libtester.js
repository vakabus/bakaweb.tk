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

	this.answers = this.answer.split('##');
}



function Test() {
	this.topic = '';
	this.description = '';
	this.questions = []

	this.partialQuestions = [];

	this.selected = -1;
	this.wrong = 0;
	this.right = 0;



	this.onStatChange = function() {};
	this.addQuestion = function(question) {
		this.questions.push(question);
	};
	this.generateXML = function() {
		this.removeEmptyQuestions();
		xml = '<?xml version="1.0" encoding="UTF-8"?>\n<test>\n\t<nadpis>' + this.topic + '</nadpis>\n\t<popis>' + this.description + '</popis>\n';
		for (var q =0; q < test.questions.length; q++) {
			xml = xml + '\t<otazka otazka="' + test.questions[q].question + '" odpoved="' + test.questions[q].answer + '" uri_obrazku="' + test.questions[q].image + '" />\n';
		}
		xml = xml + "</test>"
		return xml;
	};
	this.fillPartialQuestions  = function() {
		this.partialQuestions = this.questions.slice(0);
	};
	this.selectQuestion = function() {
		if ( this.partialQuestions.length == 0) {
			this.fillPartialQuestions();
		}
		this.selected = Math.floor(Math.random()*(this.partialQuestions.length-1));
		console.log(this.selected);
		this.onStatChange();
	};
	this.checkAnswer = function(answer) {
		if (this.partialQuestions[this.selected].answers.contains(answer.toUpperCase())) {
			//Spravna odpoved
			this.right++;
			this.partialQuestions.splice(this.selected,1);
		} else {
			//Spatna odpoved
			alert('Špatně - "'+this.partialQuestions[this.selected].answer+'"');
			this.wrong++;
		}
	};
	this.answerCurrent = function(answer) {
		this.checkAnswer(answer);
		this.selectQuestion();
	};
	this.loadXML = function(xml) {
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
	this.save = function() {
		if(typeof(Storage) !== "undefined") {
			localStorage.setItem('lastTest',JSON.stringify(this));
			console.log('saved');
		}
	};
	this.removeEmptyQuestions = function() {
		for (var x = test.questions.length-1; x > -1; x--) {
			if (test.questions[x].image == '' && test.questions[x].question == '' && test.questions[x].answer == '') {
				test.questions.splice(x,1);
			}
		}
	};
	this.load = function() {
		if(typeof(Storage) !== "undefined") {
			var old = JSON.parse(localStorage.getItem("lastTest"));
			this.selected = old.selected;
			this.topic = old.topic;
			this.description = old.description;
			this.questions = old.questions;
			this.partialQuestions = old.partialQuestions;
			this.wrong = old.wrong;
			this.right = old.right;
		};
	}
};
