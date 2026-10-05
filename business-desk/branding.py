"""Business-owned browser/installed identity; no third-party image fetches."""
import base64
import re


def display_name(business):
    return business.get('trading_name') or business.get('workspace_name') or business['name']


def brand_icon(business):
    if business.get('logo_data'): return business['logo_data']
    letters=''.join(x[0] for x in display_name(business).split()[:2]).upper()
    letters=re.sub(r'[^A-Z0-9]','',letters) or 'B'
    colours={'indigo':'#4f46e5','blue':'#2563eb','emerald':'#047857','orange':'#c2410c'}
    colour=business.get('brand_hex') or colours.get(business.get('brand_color'),'#4f46e5')
    rgb=[int(colour[i:i+2],16)/255 for i in (1,3,5)]
    rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    ink='#172033' if sum(v*w for v,w in zip(rgb,(.2126,.7152,.0722)))>.179 else '#ffffff'
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 192 192"><rect width="192" height="192" rx="40" fill="{colour}"/><text x="96" y="120" text-anchor="middle" font-family="Arial,sans-serif" font-size="72" font-weight="700" fill="{ink}">{letters}</text></svg>'
    return 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()


def manifest(business):
    name=display_name(business)
    return {'id':'/workspaces/'+business['id'],'name':name,'short_name':business.get('short_name') or name[:24],
            'description':business.get('business_description') or 'Your business workspace',
            'start_url':'/?business='+business['id'],'scope':'/','display':'standalone',
            'background_color':'#f7f8fc','theme_color':business.get('brand_hex') or '#4f46e5',
            'icons':[{'src':brand_icon(business),'sizes':'192x192','type':'image/png' if business.get('logo_data','').startswith('data:image/png') else 'image/jpeg' if business.get('logo_data') else 'image/svg+xml','purpose':'any'}]}
