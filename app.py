import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("¡SI SE VE, FLET FUNCIONA!"))
    page.add(ft.ElevatedButton("BOTON DE PRUEBA"))

if __name__ == "__main__":
    print("Intentando abrir ventana...")
    ft.app(target=main)
    print("Si ves esto en la terminal, Flet se cerró o falló.")