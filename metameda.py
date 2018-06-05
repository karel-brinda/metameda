#! /usr/bin/env python3

"""MetaMedA - meta-analysis using PubMed

Author:  Karel Brinda <kbrinda@hsph.harvard.edu>

License: MIT
"""

import argparse
import os
import sys
import requests
import re

import xml.etree.ElementTree as ET

esearch="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
efetch="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def pmids(query):
	data={
		"db":"pubmed",
		"retmax":424242,
		"term":query,
	}

	r = requests.post(esearch, data=data,)
	tree = ET.fromstring(r.text)
	idlist=tree.find("IdList")
	return [x.text for x in idlist]

def article_to_info(PubmedArticle):
	MedlineCitation=PubmedArticle.find("MedlineCitation")
	try:
		pmid=MedlineCitation.find("PMID").text
	except:
		pmid=None

	Article=MedlineCitation.find("Article")
	try:
		title=Article.find("ArticleTitle").text
	except:
		title=None

	try:
		doi=Article.find("ELocationID").text
	except:
		doi=None

	try:
		Abstract=Article.find("Abstract")
		AbstractText=[x.text for x in Abstract.iter("AbstractText")]
		text=' '.join(AbstractText)
		sentences=text.split(". ")
	except:
		sentences=[]


	return [title,pmid,doi,sentences]


def summary(query,keyword):
	pattern = re.compile(keyword, re.IGNORECASE)
	#print(pattern)

	print("Querying PubMed (\"{}\")".format(query),file=sys.stderr)
	q=pmids(query)

	print("Downloading a list of abstracts",file=sys.stderr)

	data={
		"db":"pubmed",
		"retmode":"xml",
		"id":",".join(q),
	}
	r = requests.post(efetch, data=data,)
	tree = ET.fromstring(r.text)

	articles=list(tree.iter("PubmedArticle"))


	print("""<!DOCTYPE HTML>
	<html>
	<head>
	<meta charset="UTF-8">
	<style>
		strong {{color:red;}}
	</style>
	<title>
		{title}
	</title>
	</head>
	<body>
	<h1>{title}</h1>
	<h3>{count} results</h3>
	""".format(title=query,count=len(articles)))

	print("Going through the abstracts ({})".format(len(articles)),file=sys.stderr)
	i=0
	for article in articles:
		i+=1
		(title, pmid, doi, sentences)=article_to_info(article)
		print("<h2>{}. {}</h2>".format(i, title))
		if doi is not None:
			print("""
				<a href=\"http://dx.doi.org/{doi}\">DOI.org</a> -
				<a href=\"http://dx.doi.org.ezp-prod1.hul.harvard.edu/{doi}\">Harvard DOI</a> -
			""".format(doi=doi))
		if pmid is not None:
			print("""
				<a href=\"https://www.ncbi.nlm.nih.gov/pubmed/{pmid}\">PubMed</a> -
				<a href=\"https://www-ncbi-nlm-nih-gov.ezp-prod1.hul.harvard.edu/pubmed/{pmid}\">Harvard PubMed</a>
				""".format(pmid=pmid)
			)

		sentences=list(filter(lambda x: len(x)>0, map(str.strip,sentences)))

		# correction for abbreviations
		j=0
		while j < len(sentences)-1:
			if sentences[j+1][0].islower():
				sentences[j]=". ".join([sentences[j],sentences[j+1]])
				del sentences[j+1]
			else:
				j+=1


		print("<ul>")
		for s in sentences:
			if s.lower().find(keyword.lower())!=-1:
				print("<li>{}.".format(
						pattern.sub("<strong>{}</strong>".format(keyword.upper()),s)
					))
		print("</ul>")
	print("""
	</body>
	</html>""")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="")

	parser.add_argument('query',
			type=str,
			metavar='query',
		)

	parser.add_argument('keyword',
			type=str,
			metavar='keyword',
		)

	args = parser.parse_args()

	s=summary(args.query, args.keyword)
