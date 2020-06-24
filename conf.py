cfg = {
    'from_email': 'bfichera.dev.email@gmail.com',
    'to_email': 'bfichera@mit.edu',
    'smtp_server': 'smtp.gmail.com',
    'port': 465,
    'password': 'thisismypassword',
    'terms': [
        'second\s*.\s*harmonic\s*.\s*generation',
        'nonlinear\s*.\s*optic',
        'ultrafast',
        'time.resolved',
    ],
    'chem_terms': [
        'Ca Mn2 B2',
        'Ta S2',
    ],
    'flags': [
        'IGNORECASE'
    ],
    'section': 'cond-mat.*',
    'max_results': 500,
}
