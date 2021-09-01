from pyfiglet import figlet_format
from rich.console import Console
from rich.markdown import Markdown
from sources import sources, internshala
from emailscraper import viewSkipped


def main():
    print(figlet_format('Email  Scraper'))
    print(figlet_format('          Harsh  Gupta'))
    print(figlet_format('          IEEE  VIT'))

    console = Console()
    console.print(Markdown('##### Welcome to my command line utility'))
    console.print(Markdown('###### You may enter 0 OR skip to skip any company | -1 OR exit to quit the command line utility'))


    mode = ''
    while True:
        mode = input('\nPlease select any mode to continue\nauto OR manual (manual is not recommended | but more accurate)\n').lower()
        if mode == 'auto' or mode == 'manual':
            break

    while True:
        use_module = input('\nPlease select any email scraping use_module\nemail-scraper pagkage (high accuracy | much slower) || custom email regex (less accurate | much faster)\nEnter 1 OR 2\n').lower()
        if use_module == '1' or use_module == '2':
            if use_module == "1":
                use_module = True
            else:
                use_module = False
            break


    print("\nFrom where do you wanna scrape emails\n")

    for index, source in enumerate(sources):
        print(f"{index+1}. {source.capitalize()}")

    source = ""
    while not (source.isnumeric() and int(source) in range(1, len(sources)+1)):
        source = input("\nEnter your choice\n")


    eval(sources[int(source)-1])(mode, use_module)
    viewSkipped(sources[int(source-1)].capitalize())


if __name__ == "__main__":
    main()