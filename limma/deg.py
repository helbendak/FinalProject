import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
R = robjects.r

R('library("limma")')
R('target <- read.csv("gse85499_samples.csv")')
R('log2expr <- read.csv("gse85499_log_expression.csv")')
R('design <- model.matrix(~target$disease_status)')
R('colnames(design) <- c("intercept", "CD")')
R('rownames(log2expr) <- log2expr$X')
R('log2expr$X <- NULL;')
R('fit <- lmFit(log2expr, design)')
R('fit2 <- eBayes(fit)')
genes = R('genes <- topTable(fit2, adjust="fdr", coef=2, number = 1000)')
pandas2ri.activate()
genes = pandas2ri.ri2py(genes)
R('write.csv(genes, file="gse85499_diff_genes.csv")')
