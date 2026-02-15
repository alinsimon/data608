import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg
import os

# Create reports folder if it doesn't exist
os.makedirs('reports', exist_ok=True)

# Create simple PDF presentation
pdf_filename = 'reports/IIJA_Funding_Analysis_Presentation.pdf'

with PdfPages(pdf_filename) as pdf:
    
    # Main Title Page
    fig = plt.figure(figsize=(11, 8.5))
    fig.patch.set_facecolor('white')
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    ax.text(0.5, 0.6, 'IIJA Funding Allocation Analysis', 
            ha='center', va='center', fontsize=26, fontweight='bold',
            transform=ax.transAxes)
    
    ax.text(0.5, 0.45, 'Question 1: Is the allocation equitable based on population?', 
            ha='center', va='center', fontsize=14,
            transform=ax.transAxes)
    
    ax.text(0.5, 0.38, 'Question 2: Does allocation favor the Biden administration?', 
            ha='center', va='center', fontsize=14,
            transform=ax.transAxes)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()
    
    # Question 1: Funding vs Population
    fig = plt.figure(figsize=(11, 8.5))
    fig.patch.set_facecolor('white')
    
    img = mpimg.imread('images/output_funding_vs_population_question1.png')
    ax = fig.add_subplot(111)
    ax.imshow(img)
    ax.axis('off')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()
    
    # Question 2: Political Comparison
    fig = plt.figure(figsize=(11, 8.5))
    fig.patch.set_facecolor('white')
    
    img = mpimg.imread('images/output_political_comparison_question2.png')
    ax = fig.add_subplot(111)
    ax.imshow(img)
    ax.axis('off')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

