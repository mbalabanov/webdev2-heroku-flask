from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('hello_world.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

if __name__ == '__main__':
    app.run(port=7890)
