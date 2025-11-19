# Teoretisk forståelse

**Hvad betyder det, at en maskine "lærer"?**

"Maskinen" fodres med et datsæt, og analyserer det for gentagne mønstre.

F.eks., i et datasæt med basketballstjerner, kunne man forestille sig, at den ville vurdere, at en spillers højde kunne have en indflydelse på deres performance. Der kan være enormt høje spillere som ikke er så dygtige, og der kan være lave spillere som er exceptionelt dygtige, men mønstret vil sandsynligvis stadig kunne findes.

**Hvad er forskellen på supervised og unsupervised learning?**

Supervised learning foregår på den måde, at modellen modtager et struktureret og labelled datasæt. Dvs., at modellen på forhånd har fået en forklaring på, hvilke data der er hvilke. 

I unsupervised learning, får modellen en bunke ubeskrevne data, hvor den selv må stå for blindt at finde mønstre.

**Hvorfor opdeler man i test- og træningsdata?**

For at kunne vurdere, om modellen har lavet meaningful connections og fundet de rette mønstre, ud fra de træningsdata den har fået, kan de resultater med fordel måles op mod en anden del af det oprindelige datasæt. På den måde kan man se, om modellen har fundet frem til et brugbart resultat, ved at tjekke, hvorvidt eller ej det stemmer overens med "virkeligheden".

**Hvad er forskellen på klassifikation og regression?**

I store træk arbejder regression i tal, mens klassifikation arbejder i kategorier.

En regressionsmodel kan bruges, som i mit projekt, til at forudse en pris på en diamant ud fra en række faktorer. Den udvikler altså en numerisk prediction på baggrund af data.

En klassifikationsmodel kan i stedet, igen som i mit projekt, bruges til at inddele data i kategorier, hér lavt, medium, højt prisleje. Her forudses ingen pris, men ud fra datasættet inddeles forskellige datapunkter i en kategori - eller en klasse - for sig. Heraf klassificering. 

**Hvorfor er dataforberedelse vigtig?**

Mange store datasæt kan indeholde fejlagtige eller ufuldstændige datapunkter. Som f.eks. i pingvin-datasættet, optrådte der mange tomme rækker i diverse kolonner. Dette kan være en stor svaghed for f.eks. en KNN model, som læner sig op af, at andre punkter i datasættet er af reel værdi. 

Hvis en model trænes på data, som er fejlagtige eller ufuldstændige, vil den i ringere grad have mulighed for at danne et værdifuldt overblik over givne data. 

**Hvad er overfitting og underfitting?**

Overfitting er hvad der sker med en model, når den inkorporerer for meget data. Dvs., at modellen *også* lærer af støjpunkter; ufuldstændige data, ekstreme outliers. I dette tilfælde vil modellen have sværere ved at forudse præcise resultater, da den i forvejen er farvet af en masse data, som i en generel forstand ikke er relevante. 

Underfitting er så det modsatte - hvor modellen trænes på for specifikke data, så den i sidste ende ender med at være for stringent i sin opdeling og forudsigelser. 

**Hvad betyder det, at en feature har høj korrelation, og hvorfor kan det være et problem?**

Høj korrelation mellem to datakolonner kan gøre det sværere for modellen, at skelne mellem dem, og deres sammenhænge med resten af datasættet. Dette kan resultere i overfitting, hvor modellen overser hver features reelle interaktion med andre datapunkter. 

**Hvorfor og hvordan bruger man cross-validation?**

Cross-validation kan bruges, når et enkelt split ikke ville give en præcis nok model. Det kan bruges som et evalueringsværktøj, for at se, hvor præcis modellen er over flere kørsler. 

Ved at blande træningsdataene, kan den vise hvor god modellen er til at generalisere; hvor godt den håndterer outliers.

# Praktisk:

## Saml og forbered datasæt
* Datasæt loades fra Seaborn
* Tjek for fejlagtige datapunkter
* Drop fejlagtige datapunkter, hvis de findes
* Kolonner med tekstværdi omdannes til numeriske værdier

Til klassifikation:
* Opret ny kolonne, her "price_level" med 3 niveauer;
	* high, medium, low

Til regression:
* Vælg target for prediction, i dette tilfælde kolonnen "price"

## Vælg en passende metode: 

I praksis - har prøvet forskellige modeller, og er landet på Decision Tree (regression). 

Der er pros and cons; Decision Tree modellen er dygtig til at sætte sig ind i et stort datasæt, og til at komme med en god prediction på baggrund af de data. Til gengæld kan den slås ud af nye eller meget sjældne kombinationer af data.

Vurderingen hér er, at med et datasæt af denne størrelse, over 50.000 rækker, er den passende til at kunne udvikle passende predictions.

## Træne og teste modellen: 

Datasættet splittes (20/80 test/træning) for at give modellen et stort nok datasæt til at kunne give præcise resultater, og samtidig have et betydeligt datasæt at sammenligne sine resultater med for præcisionsmålinger.

`max_depth` defineres for modellen; hvor mange "decisions" må vores decision tree foretage sig per operation? 

Jeg har testet med en range på 1-100. Oplever at præcisionen stiger stødt mellem 1-10, og kun præciseres en smule mere op til 15. Alt over 15 decisions per operation giver ikke et mærkbart afkast. 

## Evaluere præcisionen:

Mit projekt leverer en masse data;
* Præcisionsmålinger:
	* via `accuracy_score()` for klassifikationsdelen
	* via RMSE for regressionsdelen

Ydermere vises hvor mange rækker der klassificeres ind i hver kategori (high/medium/low), feature importances både for klassifikation og regression, samt følgende diagrammer:

* Feature Importances (classification) bar chart
![Feature Importances (classification) bar chart](image.png)

* Feature Importances (regression) bar chart
![Feature Importances (regression) bar chart](image-1.png)

* Actual vs Predicted Prices (regression) scatter plot
![Actual vs Predicted Prices (regression) scatter plot](image-2.png)

* Learning curve (classification)
![Learning curve (classification)](image-3.png)

* Learning curve (regression)
![Learning curve (regression)](image-4.png)

* Prisdistribution
![Prisdistribution](image-5.png)

* Karatdistribution
![Karatdistribution](image-6.png)

* Correlation heatmap for modellens værdier
![Correlation heatmap for modellens værdier](image-7.png)

# Andet

## Cross-validation

Cross-validation var ikke nyttig for regressionsdelen, da den for ofte inkorporerer outliers, til at kunne bygge en generaliserende model. Det er mere vigtigt at modellen generelt er robust over et bredt spænd, end at den skal kunne generalisere over ekstreme outliers.

For klassifikationen viser cross-validation en smule mindre præcision, dog stadig en jeg er tilfreds med.

## Stratification

For klassifikationsmodellen bruges `stratify` i datasættet. Dette gøres for at sørge for, at det sker en ligelig opdeling af data i trænings- og valideringssættene. 