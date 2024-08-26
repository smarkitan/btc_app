import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta
from dash import Dash, dcc, html, Input, Output, State, ctx

# Definește data curentă și data de început
end_date = datetime.now()
start_date = end_date - timedelta(days=36500)  # Ultimii 100 de ani pentru a acoperi toate perioadele

# Creează aplicația Dash
app = Dash(__name__)

# Layout-ul aplicației
app.layout = html.Div([
    html.H1('Bitcoin Price Evolution', style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Text box pentru simbolul criptomonedei și butonul de căutare
    html.Div([
        dcc.Input(id='crypto-symbol', type='text', value='BTC-USD', style={'marginRight': '10px', 'width': '60%'}),
        html.Button('Search Crypto', id='search-button', n_clicks=0, style={'width': '30%'})
    ], className='input-container', style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'marginBottom': '10px'}),

    # Butoanele de filtrare
    html.Div([
        html.Button('5D', id='button-5d', n_clicks=0),
        html.Button('1M', id='button-1m', n_clicks=0),
        html.Button('3M', id='button-3m', n_clicks=0),
        html.Button('6M', id='button-6m', n_clicks=0),
        html.Button('1Y', id='button-1y', n_clicks=0),
        html.Button('5Y', id='button-5y', n_clicks=0),
        html.Button('All', id='button-all', n_clicks=0),
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'marginBottom': '20px'}),

    # Graficul va fi actualizat aici
    dcc.Graph(
        id='crypto-graph',
        config={
            'displayModeBar': False,  
            'displaylogo': False,     
            'editable': False,        
            'scrollZoom': False,      
            'showTips': False,        
            'showAxisDragHandles': False,  
            'modeBarButtonsToRemove': ['zoom', 'pan', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toImage', 'sendDataToCloud'],
        },
        style={'width': '100%', 'height': '70vh'}  # Ajustează înălțimea pentru a se potrivi mai bine
    ),

    # Stocarea intervalului curent și simbolului curent
    dcc.Store(id='current-range', data={'start': None, 'end': None}),  # Stocăm intervalul curent
    dcc.Store(id='current-symbol', data='BTC-USD'),  # Stocăm simbolul curent
    dcc.Store(id='initial-load', data=True),  # Indică că aplicația s-a încărcat inițial

    # Mesajul de încărcare
    html.Div(id='loading-message', style={'textAlign': 'center', 'marginTop': '20px', 'color': 'red'})
])

@app.callback(
    [Output('crypto-graph', 'figure'),
     Output('current-range', 'data'),
     Output('current-symbol', 'data'),
     Output('initial-load', 'data'),
     Output('loading-message', 'children')],
    [Input('search-button', 'n_clicks'),
     Input('crypto-symbol', 'n_submit'),  # Noua intrare pentru n_submit
     Input('crypto-symbol', 'value'),
     Input('button-5d', 'n_clicks'),
     Input('button-1m', 'n_clicks'),
     Input('button-3m', 'n_clicks'),
     Input('button-6m', 'n_clicks'),
     Input('button-1y', 'n_clicks'),
     Input('button-5y', 'n_clicks'),
     Input('button-all', 'n_clicks'),
     Input('initial-load', 'data')],
    [State('current-range', 'data'),
     State('current-symbol', 'data')]
)
def update_graph(n_clicks_search, n_submit, symbol, n_clicks_5d, n_clicks_1m, n_clicks_3m, n_clicks_6m, n_clicks_1y, n_clicks_5y, n_clicks_all, initial_load, current_range, current_symbol):
    triggered_id = ctx.triggered_id
    loading_message = ""

    # Dacă aplicația este încă în stadiul de încărcare inițială
    if initial_load:
        loading_message = "The page is loading from a web service that has just started. Please wait..."
        symbol = 'BTC-USD'
        initial_load = False

    try:
        # Verifică dacă simbolul este setat implicit la încărcare
        if symbol is None:
            symbol = current_symbol
        
        if not symbol:
            symbol = current_symbol  # Folosește simbolul curent dacă nu este specificat
        
        if symbol != current_symbol:
            # Dacă simbolul s-a schimbat, actualizează intervalul
            current_range = {'start': None, 'end': None}

        # Descarcă datele pentru criptomoneda specificată
        df = yf.download(symbol, start=start_date, end=end_date)
        if df.empty:
            raise ValueError("No data found for the symbol")
        
        df['Date'] = df.index.date
        df['Close'] = df['Close'].round(2)
        df['Open'] = df['Open'].round(2)
        df['High'] = df['High'].round(2)
        df['Low'] = df['Low'].round(2)
        df['Volume'] = df['Volume'].apply(lambda x: f"{x:,}")
        df['Symbol'] = symbol

        # Obține informațiile despre criptomonedă
        ticker = yf.Ticker(symbol)
        crypto_info = ticker.info

        crypto_name = crypto_info.get('shortName', symbol)  # Folosește simbolul dacă numele nu este disponibil
        last_close_price = df['Close'].iloc[-1] if not df['Close'].empty else 'N/A'
        last_close_date = df['Date'].iloc[-1] if not df['Date'].empty else 'N/A'

        # Convertim datele într-un format ușor de afișat
        last_close_price_str = f"{last_close_price:.2f}" if isinstance(last_close_price, (int, float)) else last_close_price
        last_close_date_str = last_close_date.strftime('%Y-%m-%d') if isinstance(last_close_date, datetime) else last_close_date

        fig = go.Figure()

        # Adăugăm doar linia fără markeri
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Close'],
            mode='lines',  # Utilizăm doar linii fără markeri
            name=f'{symbol} - Close Price',
            text=[f"Date: {date}<br>Close: {close:.2f}<br>Open: {open:.2f}<br>High: {high:.2f}<br>Low: {low:.2f}<br>Volume: {volume}<br>Symbol: {symbol}" 
                  for date, close, open, high, low, volume in zip(df['Date'], df['Close'], df['Open'], df['High'], df['Low'], df['Volume'])],
            hoverinfo='text'
        ))

        # Setăm intervalul de timp pe baza butoanelor apăsate
        if triggered_id and triggered_id.startswith('button'):
            button_id = triggered_id
            if button_id == 'button-5d':
                new_range = {'start': df['Date'].max() - timedelta(days=5), 'end': df['Date'].max()}
            elif button_id == 'button-1m':
                new_range = {'start': df['Date'].max() - timedelta(days=30), 'end': df['Date'].max()}
            elif button_id == 'button-3m':
                new_range = {'start': df['Date'].max() - timedelta(days=93), 'end': df['Date'].max()}
            elif button_id == 'button-6m':
                new_range = {'start': df['Date'].max() - timedelta(days=182), 'end': df['Date'].max()}
            elif button_id == 'button-1y':
                new_range = {'start': df['Date'].max() - timedelta(days=365), 'end': df['Date'].max()}
            elif button_id == 'button-5y':
                new_range = {'start': df['Date'].max() - timedelta(days=1825), 'end': df['Date'].max()}
            elif button_id == 'button-all':
                new_range = {'start': df['Date'].min(), 'end': df['Date'].max()}

            # Actualizează graficul cu intervalul de timp selectat
            fig.update_xaxes(range=[new_range['start'], new_range['end']])

            # Salvează intervalul curent
            current_range = new_range

        else:
            # Dacă nu este niciun buton apăsat, utilizează intervalul de timp curent
            if current_range['start'] and current_range['end']:
                fig.update_xaxes(range=[current_range['start'], current_range['end']])
            else:
                # Setează intervalul inițial
                current_range = {'start': df['Date'].min(), 'end': df['Date'].max()}
                fig.update_xaxes(range=[current_range['start'], current_range['end']])

        fig.update_layout(
            title=f'Price evolution for {crypto_name} ({symbol})<br>Last Close: {last_close_price_str} on {last_close_date_str}',
            title_x=0.5,  # Centrează titlul
            xaxis=dict(tickformat='%Y-%m-%d'),
            margin=dict(l=10, r=10, t=100, b=40)  # Ajustează marginile pentru a oferi spațiu pentru titlu
        )

        # După încărcarea datelor, ștergem mesajul de încărcare
        loading_message = ""

    except Exception as e:
        # Dacă există o eroare, arată un grafic gol cu mesajul de eroare
        fig = go.Figure()
        fig.update_layout(
            title=f'Error: {str(e)}',
            xaxis=dict(tickformat='%Y-%m-%d'),
            margin=dict(l=10, r=10, t=100, b=40)  # Ajustează marginile pentru a oferi spațiu pentru titlu
        )
        # Asigurăm că intervalul și simbolul sunt definite
        current_range = {'start': start_date.date(), 'end': end_date.date()}
        current_symbol = 'BTC-USD'  # Folosește simbolul default în caz de eroare

    return fig, current_range, current_symbol, initial_load, loading_message

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=10000, debug=False)
