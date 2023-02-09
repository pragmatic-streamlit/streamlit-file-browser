import py3Dmol
from stmol import showmol
from rdkit import Chem
import streamlit as st
import streamlit.components.v1 as components
import os

def show_protein(protein_path, height=300):
    view = py3Dmol.view(width='100%', height=height)
    view.addModel(open(protein_path, 'r').read(), os.path.splitext(protein_path)[-1][1:])
    view.setStyle({"cartoon": {'color': 'spectrum'}})
    view.zoomTo()
    # view.spin()
    show_molecule(view, height=height)

def show_ligand(ligand_path, height=300):
    view = py3Dmol.view(width='100%', height=height)
    view.addModel(open(ligand_path, 'r').read(), os.path.splitext(ligand_path)[-1][1:])
    view.setStyle({},{'stick':{'colorscheme':'cyanCarbon','radius':0.2}})
    view.zoomTo() 
    # view.spin()
    show_molecule(view, height=height)


def show_molecule(view, height=500):
    pre_html = """
        <style>
        body {
        background: white;
        border: 1px solid rgb(233 232 231);
        margin: 1px;
        }
        .fullscreen-button {
        position: absolute;
        z-index: 100;
        top:  5px;
        right:  5px;
        background: rgba(0,0,0,0.05);
        border:  0;
        width:  40px;
        height:  40px;
        border-radius: 50%;
        box-sizing: border-box;
        transition:  transform .3s;
        font-size: 0;
        opacity: 1;
        pointer-events: auto;
        cursor:  pointer;
        }
        .fullscreen-button:hover {
        transform: scale(1.125);
        }
        .fullscreen-button span {
        background: white;
        width:  4px;
        height:  4px;
        border-top:  2.5px solid #111; /* color */
        border-left:  2.5px solid #111; /* color */
        position: absolute;
        outline: 1px solid transparent;
        -webkit-backface-visibility: hidden;
        transform: translateZ(0);
        will-change: transform;
        -webkit-perspective: 1000;
        transition:  .3s;
        transition-delay: .75s;
        }
        .fullscreen-button span:nth-child(1) {
        top: 11px;
        left: 11px;
        }
        .fullscreen-button span:nth-child(2) {
        top: 11px;
        left: 22px;
        transform: rotate(90deg);
        }
        .fullscreen-button span:nth-child(3) {
        top: 22px;
        left: 11px;
        transform: rotate(-90deg);
        }
        .fullscreen-button span:nth-child(4) {
        top: 22px;
        left: 22px;
        transform: rotate(-180deg);
        }

        /* Fullscreen True
        ------------------------------*/
        [fullscreen] .fullscreen-button span:nth-child(1) {
        top: 22px;
        left: 22px;
        }
        [fullscreen] .fullscreen-button span:nth-child(2) {
        top: 22px;
        left: 11px;
        }
        [fullscreen] .fullscreen-button span:nth-child(3) {
        top: 11px;
        left: 22px;
        }
        [fullscreen] .fullscreen-button span:nth-child(4) {
        top: 11px;
        left: 11px;
        }

        /* Dark Style
        ------------------------------*/
        [light-mode=dark] {
        background: #111;
        color:  #fff;
        }
        [light-mode=dark] .fullscreen-button {
        background: rgba(255,255,255,.05);
        }

        [light-mode=dark] .fullscreen-button span {
        border-top:  2.5px solid #fff;
        border-left:  2.5px solid #fff;
        }
        .center {
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        background: #000;
        }
        .wave {
        width: 5px;
        height: 100px;
        background: linear-gradient(45deg, cyan, #fff);
        margin: 10px;
        animation: wave 1s linear infinite;
        border-radius: 20px;
        }
        .wave:nth-child(2) {
        animation-delay: 0.1s;
        }
        .wave:nth-child(3) {
        animation-delay: 0.2s;
        }
        .wave:nth-child(4) {
        animation-delay: 0.3s;
        }
        .wave:nth-child(5) {
        animation-delay: 0.4s;
        }
        .wave:nth-child(6) {
        animation-delay: 0.5s;
        }
        .wave:nth-child(7) {
        animation-delay: 0.6s;
        }
        .wave:nth-child(8) {
        animation-delay: 0.7s;
        }
        .wave:nth-child(9) {
        animation-delay: 0.8s;
        }
        .wave:nth-child(10) {
        animation-delay: 0.9s;
        }

        @keyframes wave {
        0% {
            transform: scale(0);
        }
        50% {
            transform: scale(1);
        }
        100% {
            transform: scale(0);
        }
        }
        </style>
    """
    pre_html += f"<script>window.viewerHeight={height}</script>"
    pre_html += """
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.3/jquery.min.js" integrity="sha512-STof4xm1wgkfm7heWqFJVn58Hm3EtS31XFaagaa8VMReCXAkQnJZ+jEy8PCC/iT18dFy95WcExNHFTqLyp72eQ==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery-fullscreen-plugin/1.1.5/jquery.fullscreen-min.min.js" integrity="sha512-G+eTBPYlf902hmapQBhcLjWVbGC2FFtJeHYlxW/biC5MRmvYiL7wioEKXuel40Y1tZ/u9jMUzZXyrDJn8rTjiQ==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
        <script>
            function go_fullscreen(elem){
                const v = $(elem.nextElementSibling)
                v.fullScreen(true).height('100%').css('min-height', window.viewerHeight + 'px');
                return false;
            }
        </script>
        <div id="loading" class="center">
            <div class="wave"></div>
            <div class="wave"></div>
            <div class="wave"></div>
            <div class="wave"></div>
            <div class="wave"></div>
            <div class="wave"></div>
            <div class="wave"></div>
            <div class="wave"></div>
            <div class="wave"></div>
            <div class="wave"></div>
        </div>
        <button class="fullscreen-button" onclick="go_fullscreen(this)">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
        </button>
    """
    post_html = """
    <script>
        if(typeof $3Dmolpromise !== 'undefined') {
            $3Dmolpromise.then(function() {
                $('#loading').fadeOut(1000);
            })
        }
    </script>
    """
    components.html(pre_html + view._make_html() + post_html, height=height + 3)