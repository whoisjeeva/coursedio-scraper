import os


class Npm:
    def __init__(self):
        self.package_string = """{
  "name": "__NAME__",
  "version": "1.0.1",
  "description": "",
  "main": "index.js",
  "scripts": {
  },
  "author": "",
  "license": "ISC"
}"""
    
    def publish(self, slug, path):
        os.chdir(path)
        with open("package.json", "w") as f:
            f.write(self.package_string.replace("__NAME__", "coursedio-" + slug))
        
        with open("index.js", "w") as f:
            f.write("console.log('coursedio');")
            
        os.system("npm publish")
        

if __name__ == "__main__":
    npm = Npm()
    npm.publish("hello", "hello")
