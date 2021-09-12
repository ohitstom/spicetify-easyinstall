import os

from colorama import Fore, init

from modules import core, globals, utils

if __name__ == "__main__":
    init()
    os.system("mode con: cols=90 lines=30")
    os.system("title " + "Spicetify Easyinstall")

    while True:
        try:
            print(f"{Fore.MAGENTA}\n"
                  f"[Startup]\n"
                  f"\n{Fore.GREEN}"
                  f" 1) Install\n"
                  f"\n"
                  f" 2) Update Config\n"
                  f"\n"
                  f" 3) Download Latest Themes And Extensions\n"
                  f"\n"
                  f" 4) Uninstall\n"
                  f"{Fore.MAGENTA}")

            try:
                launch = int(input("Choose From The List Above (1-4): "))
            except Exception:
                os.system("cls")
                print(f"{Fore.RED}[!] INVALID OPTION! Make Sure To Choose A (WHOLE) Number Corresponding To Your Choice [!]")
                continue

            os.system("cls")

            if launch == 1:
                core.install()
                return_start = input(f"{Fore.MAGENTA}\nReturn To Startup? Y/N: ")
                if return_start.lower() in ["n", "no"]:
                    break
                os.system("cls")

            elif launch == 2:
                core.update_config()
                break

            elif launch == 3:
                core.update_addons()
                return_start = input(f"{Fore.MAGENTA}\nReturn To Startup? Y/N: ")
                if return_start.lower() in ["n", "no"]:
                    break
                os.system("cls")

            elif launch == 4:
                core.uninstall()
                break

            else:
                print(f"{Fore.RED}[!] INVALID OPTION! Please Make Sure To Choose A Valid Option (1-4) [!]")

        except Exception as e:
            os.system("cls")
            print(f"{Fore.RED}[!]{e}[!]")
