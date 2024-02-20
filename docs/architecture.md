


### Project.Structure -- Last update: 20230607
---

- data
	- thesaurus
		- levels <!--study.levels-->
		- popular <!--most.popular 5000, 6000, 8000, 10000, etc.-->
		- general <!--general.living, source from popular TV/Movie/TalkShows, Songs, Novels, etc.-->
		- legal <!--legal.area-->
		- economic <!--economic.area-->
		- IT <!--internet.technology.area-->
		- finance <!--finance.area-->
		- crypto <!--virtual.crypto.area-->
		- math

- src
	- lib
		- io.py
		- chars.py
	- utils
		- plot.py
		- voice.py
		- image.py
	- core
		- paper.py <!--download and parse paper content.-->
		- thesaurus.py
		- ui.py
		- card.py
		- check.py -- **randomize**
			- root -> definition -> example
			- root -> word|phrase|idiom|abbr|synonym|antonym|antonym|homonyms|homographs
			- word -> root|stem|prefix|infix|suffix
		- quiz.py

	- run
		- config.py
		- app.py
		- api.py
		
- tests
- out
	- log
	- debug
	- tmp



# Tech Stack


## Python


- Data Interactive Visualization
    - https://github.com/bokeh/bokeh
    - https://github.com/plotly/plotly.py
    - Word.Cloud
        - https://github.com/amueller/word_cloud

- Text-to-Speech
    - https://github.com/coqui-ai/TTS
    - https://github.com/nateshmbhat/pyttsx3


# 20240127

- Project.WordSpark
    - http.client
        - https://github.com/seanmonstar/reqwest
    - struct.logging
        - https://github.com/tokio-rs/tracing
    - cross-platform.gui
        - https://github.com/emilk/egui
            - https://github.com/tauri-apps/tauri
            - https://github.com/slint-ui/slint
    - interactive.plotting
        - https://github.com/yuankunzhang/charming
            - https://github.com/plotters-rs/plotters
            - https://github.com/blitzarx1/egui_graphs
    - nlp
        - https://www.nltk.org/howto/wordnet.html
            - https://github.com/argilla-io/spacy-wordnet
        - https://github.com/explosion/spaCy
            - https://github.com/PyO3/pyo3
            - https://github.com/rayon-rs/rayon
            - https://github.com/rust-lang-nursery/lazy-static.rs
        - wait...
            - https://github.com/bminixhofer/nlprule
            - https://github.com/huggingface/tokenizers
            - https://github.com/guillaume-be/rust-bert
    - data
        - Patent
            - https://github.com/daneads/pypatent
            - https://github.com/eliserust/Patent_Project
            - https://github.com/anvaari/patent-crawler
        - Paper
            - https://github.com/ferru97/PyPaperBot
            - https://github.com/ppwwyyxx/SoPaper
            - https://github.com/SilenceEagle/paper_downloader
        - News
            - https://github.com/Iceloof/GoogleNews


# 20240220


- GUI.Plot.Color
    - Libs
        - `https://github.com/slint-ui/slint`
        - `https://github.com/asny/three-d`
        - `https://github.com/sebcrozet/kiss3d`
    - Graph
        - 2d -> tree.node.Card
        - 3d - Example: `https://github.com/Inspirateur/wordcloud-rs`

- Core
    - Events
        - Data
        - User
        - Statistics
