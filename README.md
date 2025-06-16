# Un VideoJuego con Backend

Este repositorio es contiene los archivos de un juego en Unity, igual como una aplicacion Flask que sirve como el backend para el juego.

El juego está basado en un juega de mesa real que se llama 'Flash Point Fire Rescue', donde el tablero contiene un edificio en riesgo de quemarse, y los bomberos (los jugadores) tienen que entrar al edificio y tomar deciciones inteligentes para encontrar a las víctimas y rescatarlas al traerlas fuera del edificio.

## Correr el Backend

Para correr la app de Flask, solo entra desde el terminal al directorio de J360_Backend y ejecuta el siguiente comando:

    '''bash
    python3 server.py
    '''

Y una vez que está corriengo, estás bien.

## Jugar FirePoint en Unity

Desde Unity Hub, agrega un proyecto desde el disk y entra el directorio 'Fire Rescue'. Ahí están los archivos necesarios para que puedas abrir el juego en Unity.

Luego, desde Unity, corre el juego, y con el servidor de Flask corriendo en localhost, el juego te esperará a que inicies el juego tecleando 'S', y luego tendrás que teclar 'A' o 'I' para elegir el modo de juego que quieres jugar: bomberos que se mueven **a**leatoriamente, o los que son **i**nteligentes.

Ahora se presentará el juego frente a ti, donde tu vista está desde arriba del tablero, podrás ver todo, como se van generando y expandiendo los fuegos y humos, y como se mueven los bomberos. 

Ve tecleando 'N' para jugar. Se te presentará el nuevo estado del juego cada vez, hasta que pase una de 3 cosas:

1. Hay 7 o más'Saved Victims'
2. Hay 4 o más 'Lost Victims'
3. Hay 24 o más 'Total Damage', se refiere al edificio

