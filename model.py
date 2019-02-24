# this include model that predict if news suggest stock price changes in near future
import pandas as pd
import pickle
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'  # https://github.com/dmlc/xgboost/issues/1715


def text_cleaner(text):
    text = text.lower()
    text = text.replace("-", " ")
    return text


class Model:
    def __init__(self):
        self.model = None
        self.count_vec, self.tfidf_vec, self.full_count, self.svd_obj, self.feature_names = \
            None, None, None, None, None

    def fit_bow(self, titles):
        """
        :param titles: (list of str)
        """
        from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
        # self.count_vec = CountVectorizer(tokenizer=lambda x: x.split(), ngram_range=(1, 2), stop_words=None)
        # self.tfidf_vec = TfidfVectorizer(tokenizer=lambda x: x.split(), ngram_range=(1, 2), stop_words=None)
        self.count_vec = CountVectorizer(ngram_range=(1, 2), stop_words=None)
        self.tfidf_vec = TfidfVectorizer(ngram_range=(1, 2), stop_words=None)
        self.count_vec.fit(titles)

    def transfer_bow(self, titles):
        """
        :param titles: (list of str)
        :return: (scipy.sparse.csr.csr_matrix)
        """
        count = self.count_vec.transform(titles)
        return count

    def fit_reduced_bow(self, bow, n_comp=10):
        """
        :param bow: (scipy.sparse.csr.csr_matrix)
        :param n_comp: number of dimensions after pca (int)  
        """
        from sklearn.decomposition import TruncatedSVD
        self.svd_obj = TruncatedSVD(n_components=n_comp, algorithm='arpack')
        self.svd_obj.fit(bow.asfptype())  # change int to float, as svd does not accept int type
        feature_names = ['svd_brand_' + str(i) for i in range(n_comp)]
        return feature_names

    def transfer_reduced_bow(self, bow, n_comp=10):
        """
        :param bow: (scipy.sparse.csr.csr_matrix)
        :param n_comp: number of dimensions after pca (int)
        :return: (pandas.core.frame.DataFrame)
        """
        reduced_bow = pd.DataFrame(self.svd_obj.transform(bow.asfptype()))
        reduced_bow.columns = ['svd_brand_' + str(i) for i in range(n_comp)]
        return reduced_bow

    def dataframe_to_dmatrix(self, X, y):
        """
        :param X: (pandas.core.frame.DataFrame) 
        :param y: (pandas.core.series.Series)
        :return: (xgb Dmatrix)
        """
        import xgboost as xgb
        return xgb.DMatrix(X, label=y, feature_names=self.feature_names)

    def prepare_data(self, data_path, use_resample=False):

        df = pd.read_csv(data_path)  # "../input/news_price_records.csv"
        df = df.dropna()
        df['y'] = (df["e_price"] - df["s_price"]) / df["s_price"] > 0.01  # create y
        df["title"] = df["title"].apply(lambda x: text_cleaner(x))

        # split train and validation
        train_df = df[-20001:-1].reset_index()
        test_df = df[:-20001].reset_index()
        print("train set size:", train_df.shape[0])
        print("test set size: ", test_df.shape[0])

        self.fit_bow(df["title"].values.tolist())
        full_bow = self.transfer_bow(df["title"].values.tolist())
        train_bow = self.transfer_bow(train_df["title"].values.tolist())
        test_bow = self.transfer_bow(test_df["title"].values.tolist())

        self.feature_names = self.fit_reduced_bow(full_bow)
        train_reduced_bow = self.transfer_reduced_bow(train_bow)
        test_reduced_bow = self.transfer_reduced_bow(test_bow)

        y = train_df['y']
        from sklearn.model_selection import train_test_split
        Xtr, Xv, ytr, yv = train_test_split(train_reduced_bow.values, y, test_size=0.2, random_state=1992)

        # make train data balanced
        if use_resample:
            from imblearn.over_sampling import SMOTE
            smote = SMOTE(random_state=333)
            Xtr, ytr = smote.fit_sample(Xtr, ytr)

        # transfer to xgb accepatable form
        dtrain = self.dataframe_to_dmatrix(Xtr, ytr)
        dvalid = self.dataframe_to_dmatrix(Xv, yv)
        watchlist = [(dtrain, 'train'), (dvalid, 'valid')]

        return dtrain, watchlist

    @staticmethod
    def train_xgboost(dtrain, watchlist):
        import xgboost as xgb
        import time
        start = time.time()
        xgb_par = {'min_child_weight': 14, 'eta': 0.03, 'colsample_bytree': 0.5, 'max_depth': 14,
                   'subsample': 0.9,
                   'lambda': 0.0,  # L2 regularization
                   'alpha': 2.0,   # L1 regularization
                   'booster': 'gbtree', 'silent': 1,
                   'eval_metric': 'logloss', 'objective': 'binary:logistic'}

        model = xgb.train(xgb_par, dtrain, 80, watchlist, early_stopping_rounds=60,
                          maximize=False, verbose_eval=20)
        print('Modeling logloss %.5f' % model.best_score)
        print("Time taken in training is {}.".format((time.time() - start) / 60))
        return model

    def train_model(self, data_path):
        dtrain, watchlist = self.prepare_data(data_path)
        self.model = self.train_xgboost(dtrain, watchlist)

    def predict(self, texts):
        """
        predict if news are to suggest rise in stock price
        need to get xgboost model, bow_vocabulary, reduced_vocabulary_projection, reduced_dim_names,
        either by training model or loading a trained model
        :param texts: (list of str) 
        :return: 
        """
        if self.model is None:
            print("please train or load xgboost model first")
            return

        train_bow = self.transfer_bow(texts)
        train_reduced_bow = self.transfer_reduced_bow(train_bow)
        d = self.dataframe_to_dmatrix(train_reduced_bow, None)
        pred_prob = self.model.predict(d)
        return pred_prob

    def save_model(self, model_filename=None):
        if model_filename is None:
            from datetime import datetime
            now = datetime.now()
            model_filename = "model_" + now.strftime("%Y-%m-%d_%H-%M") + ".pickle"

        with open(model_filename, "wb") as f:
            # pickle can't load function defined by lambda,
            # e.g. CountVectorizer(tokenizer=lambda x: x.split(), ngram_range=(1,2), stop_words=None) can be pickled
            pickle.dump((self.model, self.count_vec, self.svd_obj, self.feature_names), f)
        print('model save to file "{}".'.format(model_filename))

    def load_model(self, model_filename):
        with open(model_filename, 'rb') as f:
            self.model, self.count_vec, self.svd_obj, self.feature_names = pickle.load(f)