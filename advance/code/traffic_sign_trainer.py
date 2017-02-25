#  GLib-GIO-Message: Using ...
#     http://stackoverflow.com/questions/38963373/how-can-i-fix-this-error-gtk-warning-gmodule-initialization-check-faile
#     https://software.intel.com/en-us/forums/intel-distribution-for-python/topic/691231

# to start in jupyter:
#   root@user: cd /opt/anaconda3/bin  ./jupyter notebook /root/share/project/udacity/project2_01/CarND-Traffic-Sign-Classifier-Project/Traffic_Sign_Classifier.ipynb
#

# reference answer
#    https://github.com/udacity/CarND-Traffic-Sign-Classifier-Project
#    https://www.google.co.jp/search?q=udacity+traffic+sign&oq=udacity+traffic+sign&aqs=chrome..69i57j69i60l2.8695j0j8&sourceid=chrome&ie=UTF-8
#
#


from data import *
from net.common import *
from net.blocks import *
from net.densenet import DenseNet_3 as make_net



def schdule_by_step( r, steps=(0,100), items=(0.1,0.01)):

    item = items[0]
    N=len(steps)
    for n in range(N):
        if r >= steps[n]:
            item = items[n]
    return item



def test_net( datas, labels, batch_size, data, label, loss, metric, sess):

    num = len(datas)
    all_loss = 0
    all_acc = 0
    all = 0
    for n in range(0, num, batch_size):
        #print('\r  evaluating .... %d/%d' % (n, num), end='', flush=True)
        start = n
        end = start+batch_size if start+batch_size<=num else num
        batch_datas  = datas  [start:end]
        batch_labels = labels [start:end]

        fd = {data: batch_datas, label: batch_labels, IS_TRAIN_PHASE : False}
        test_loss, test_acc = sess.run([loss, metric], feed_dict=fd)

        a = end-start
        all += a
        all_loss += a*test_loss
        all_acc  += a*test_acc

    assert(all==num)
    loss = all_loss/all
    acc  = all_acc/all

    return loss, acc



def run_train():

    # output dir, etc
    out_dir =  '/root/share/out/udacity/20'
    makedirs(out_dir+'/check_points')
    makedirs(out_dir+'/tf_board'    )
    #empty(out_dir+'/check_points')

    log = Logger()  # log file
    log.open(out_dir+'/log.txt', mode='a')
    log.write('--- [START %s] %s\n' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '-' * 64))
    log.write('\n')
    log.write('** some experiment setting **\n')
    log.write('\tSEED    = %u\n' % SEED)
    log.write('\tfile    = %s\n' % __file__)
    log.write('\tout_dir = %s\n' % out_dir)
    log.write('\n')



    # data -------------------------------------------------------------------------
    log.write('** some data setting **\n')

    preprocess = preprocess_simple    #preprocess_hist   #pre_process_ycrcb   #pre_process_simple  #pre_process_whiten
    classnames, train_images, train_labels, valid_images, valid_labels, test_images, test_labels = load_data()
    #train_images = preprocess(train_images)
    #valid_images = preprocess(valid_images)
    #test_images  = preprocess(test_images)

    num_class = 43
    _, height, width, channel = train_images.shape
    num_train = len(train_images)
    num_valid = len(valid_images)
    num_test  = len(test_images)

    train_images, train_labels = extend_data_by_flipping(train_images, train_labels)


    keep = 0.20   # 0.50   0.25 0.20   #0.15
    num_per_class = 20000
    #argument_images, argument_labels = shuffle_data_uniform(train_images, train_labels, num_class, num_per_class=num_per_class)
    #argument_images = make_perturb_images(argument_images, keep=keep)  #0.50
    #show_data(argument_images, argument_labels, classnames, 100)

    log.write('\theight, width, channel = %d, %d, %d\n'%(height, width, channel))
    log.write('\tnum_test  = %d\n'%num_test)
    log.write('\tnum_valid = %d\n'%num_valid)
    log.write('\tnum_train = %d\n'%num_train)
    log.write('\tnum_train (after flip)= %d\n' % len(train_images))
    log.write('\tnum_argument = %d\n' % (num_per_class*num_class))  #len(argument_images))
    log.write('\n')



    # net and solver -----------------------------------------------
    logit = make_net(input_shape =(height, width, channel), output_shape=(num_class))
    data  = tf.get_default_graph().get_tensor_by_name('input:0')
    label = tf.placeholder(dtype=tf.int32, shape=[None])
    prob  = tf.nn.softmax(logit)

    #define loss
    l2     = l2_regulariser(decay=0.0005)
    loss   = cross_entropy(logit, label)
    metric = accuracy(prob, label)

    #solver
    epoch_log = 2

    max_run    = 9
    batch_size = 128  #128  #256 #96  384  #128
    steps = (0, 3, 6, 8)  ##(0, 8, 10, 11)
    rates = (0.1, 0.01,  0.001, 0.0001)  ##(0.1, 0.01, 0.001, 0.0001)


    learning_rate = tf.placeholder(tf.float32, shape=[])
    solver = tf.train.MomentumOptimizer(learning_rate=learning_rate, momentum=0.9)
    solver_step = solver.minimize(loss+l2)

    log.write('** some solver setting **\n')
    log.write('\tbatch_size = %d\n'%batch_size)
    log.write('\tmax_run  = %d\n'%max_run)
    log.write('\tsteps    = %s\n'%str(steps))
    log.write('\trates    = %s\n'%str(rates))
    log.write('\n')
    log.write('\tkeep     = %f\n'%keep)
    log.write('\tnum_per_class = %d\n'%num_per_class)
    log.write('\n')

    # start training here ------------------------------------------------

    sess = tf.InteractiveSession()
    with sess.as_default():
        tf.global_variables_initializer().run( feed_dict = {IS_TRAIN_PHASE : True } )
        saver  = tf.train.Saver()
        writer = tf.summary.FileWriter(out_dir + '/tf', graph=tf.get_default_graph())


        # keep a record
        log.write('** net constuction source: **\n')
        import inspect
        source_list = inspect.getsourcelines(make_net)
        for line in source_list[0]:
            log.write(line)
        log.write('-------------------------------\n')
        log.write('\n')

        all, all_mac, all_param_size = print_macs_to_file()
        log.write('\n')
        log.write('net summary : \n')
        log.write('\tnum of conv     = %d\n'%all)
        log.write('\tall mac         = %.1f (M)\n'%all_mac)
        log.write('\tall param_size  = %.1f (M)\n'%all_param_size)
        log.write('\n')

        log.write('\n')
        log.write(' run  epoch   iter    rate      |  train_loss    (acc)     |  valid_loss    (acc)     |     \n')
        log.write('--------------------------------------------------------------------------------------------\n')

        tic = timer()
        iter = 0
        for r in range(max_run):
            rate = schdule_by_step(r, steps=steps, items=rates)

            argument_images, argument_labels = shuffle_data_uniform(train_images, train_labels, num_class,  num_per_class=num_per_class)
            argument_images = make_perturb_images(argument_images, keep=keep)
            if 0: ##<debug>
                show_data(argument_images, argument_labels, classnames, 10)


            num_argument = len(argument_images)
            N = max(num_argument//batch_size-1,1)
            #iter_log = round(float(num_train) / float(num_argument) * float(N))
            iter_log = max(round(float( epoch_log *num_train ) / float(batch_size)),1)
            for n in range(N):
                iter  = iter + 1
                run   = r + float(n)/float(N)
                epoch = float(iter*batch_size)/float(num_train)

                batch_datas, batch_labels = generate_train_batch_next( argument_images, argument_labels, n, batch_size )

                fd = {data: batch_datas, label: batch_labels, learning_rate: rate, IS_TRAIN_PHASE : True }
                _, batch_loss, batch_acc, = sess.run([solver_step, loss, metric ],feed_dict=fd)

                log.write('\r')
                log.write('%4.1f  %5.1f   %05d   %f  |  %f    (%f)  ' %
                          (run, epoch, iter, rate, batch_loss, batch_acc), is_file=0)
                #print('%05d   %f    %f    (%f)' % (iter, rate, train_loss, 0), end='\n',flush=True)


                #do validation here!
                if iter%iter_log==0:
                ##if iter%iter_log==0 or n == N-1:
                ##if n == N-1:
                    toc = timer()
                    sec_pass = toc - tic
                    min_pass = sec_pass/60.

                    #validation
                    val_loss, val_acc  = test_net(valid_images, valid_labels, batch_size, data, label, loss, metric, sess)
                    log.write('\r')
 
                    log.write('%4.1f  %5.1f   %05d   %f  |  %f    (%f)  |  %f    (%f)  | %4.1f min  \n' %
                          (run, epoch, iter, rate, batch_loss, batch_acc, val_loss, val_acc, min_pass))


                pass

            # save intermediate checkpoint
            saver.save(sess, out_dir + '/check_points/%06d.ckpt'%r)  #iter

        #final test! ------------------------------------------
        # save final checkpoint
        saver.save(sess, out_dir + '/check_points/final.ckpt')

        log.write('\n')
        log.write('** evaluation on test set **\n' )
        test_loss, test_acc = test_net(test_images, test_labels, batch_size, data, label, loss, metric, sess)
        log.write('\rtest_loss=%f    (test_acc=%f)\n' % ( test_loss, test_acc))

        log.write('\n')
        log.write('sucess\n')



def run_test():

    # output dir, etc
    out_dir = '/root/share/out/udacity/05'

    # data -------------------------------------------------------------------------
    print('read data:\n')
    classnames, train_images, train_labels, valid_images, valid_labels, test_images, test_labels = load_data()

    preprocess = preprocess_simple
    train_images = preprocess(train_images)
    valid_images = preprocess(valid_images)
    test_images  = preprocess(test_images)

    num_class = 43
    _, height, width, channel = train_images.shape
    num_train = len(train_images)
    num_valid = len(valid_images)
    num_test  = len(test_images)

    # net  -----------------------------------------------
    logit = make_net(input_shape=(height, width, channel), output_shape=(num_class))

    # data  = tf.placeholder(dtype=tf.float32, shape=[None, height, width, channel])
    data  = tf.get_default_graph().get_tensor_by_name('input:0')
    label = tf.placeholder(dtype=tf.float32, shape=[None])
    prob  = tf.nn.softmax(logit)
    loss  = cross_entropy(logit, label)
    metric = accuracy(prob, label)

    # start testing here ------------------------------------------------

    sess = tf.InteractiveSession()
    with sess.as_default():
        saver  = tf.train.Saver()
        #saver.restore(sess, out_dir + '/check_points/final.ckpt')
        saver.restore(sess, out_dir + '/check_points/final.ckpt')

        # shuffle and test using difference batch size (just make sure there is not bug!)
        print('** evaluation on test set **')
        for i in range(10):
            images,  labels = shuffle_data(test_images, test_labels)
            batch_size =  np.random.randint(1, 256)
            test_loss, test_acc = test_net(images, labels, batch_size, data, label, loss, metric, sess)
            print('  %d,   batch_size=%3d  : %f    (%f)' % (i,batch_size,test_loss, test_acc))




def run_extra_test():

    # output dir, etc
    out_dir  = '/root/share/out/udacity/08'
    data_dir = '/root/share/project/udacity/project2_01/data'
    # ----------------------------------------
    # data_dir = '/root/share/project/udacity/project2_01/data'
    # classname_file = data_dir + '/signnames.csv'
    # classnames = []
    # with open(classname_file) as _f:
    #     rows = csv.reader(_f, delimiter=',')
    #     next(rows, None)  # skip the headers
    #     for i, row in enumerate(rows):
    #         assert (i == int(row[0]))
    #         classnames.append(row[1])
    #
    classnames, train_images, train_labels, valid_images, valid_labels, test_images, test_labels = load_data()
    height, width, channel = 32, 32, 3
    num_class = 43

    #prepare data ----------------------------------------------
    test_files = ['0004.jpg',  # normal
                  '0000.jpg',  # normal
                  '0007.jpg',  # occluded with snow
                  '0006.jpg',  # small
                  '0005.jpg',  # not in class
                  ]
    test_rois = [(54, 180, 125, 260), (160, 430, 207, 469), (181, 32, 321, 142), (226, 65, 242, 78),
                 (388, 408, 700, 676)]
    num = len(test_files)
    print('num=%d' % num)

    # crop roi to 32x32
    results_image  = 255. * np.ones(shape=(1 * height, num * width, channel), dtype=np.float32)
    results_image1 = 255. * np.ones(shape=(1 * 320, num * 320, channel), dtype=np.float32)
    crops = np.zeros(shape=(num, height, width, channel), dtype=np.float32)
    for n in range(num):
        img = cv2.imread(data_dir + '/extra/' + test_files[n], 1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
        x1, y1, x2, y2 = test_rois[n]
        crop = cv2.resize(img[y1:y2, x1:x2, :], (0, 0), fx=32. / (x2 - x1), fy=32. / (y2 - y1),
                          interpolation=cv2.INTER_CUBIC)

        crop = np.clip(crop, 0, 255)
        crops[n] = crop
        insert_subimage(results_image, crop, 0, n * width)

        # mak roi and show
        H, W, C = img.shape
        S = max(H, W)
        f = 320. / S
        norm_img = cv2.resize(img, (0, 0), fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
        cv2.rectangle(norm_img, (round(f * x1), round(f * y1)), (round(f * x2), round(f * y2)), (255, 255, 0), 3)
        insert_subimage(results_image1, norm_img, 0, n * 320)
        imshow('crop', crop)
        imshow('img', img)
        cv2.waitKey(1)

    cv2.imwrite(data_dir + '/extra/' + 'crops.jpg', cv2.cvtColor(results_image, cv2.COLOR_BGR2RGB))
    # imshow('results_image', results_image)
    # imshow('results_image1', results_image1)
    # cv2.waitKey(1)



    #net  -----------------------------------------------
    logit = make_net(input_shape=(height, width, channel), output_shape=(num_class))

    # data  = tf.placeholder(dtype=tf.float32, shape=[None, height, width, channel])
    data = tf.get_default_graph().get_tensor_by_name('input:0')
    label = tf.placeholder(dtype=tf.float32, shape=[None])
    prob = tf.nn.softmax(logit)
    # top_k = tf.nn.top_k(prob, k=5)


    # start testing here ------------------------------------------------


    # sess = tf.InteractiveSession()
    # with sess.as_default():
    #     print('** test on extra **')
    #
    #     # saver = tf.train.Saver()
    #     # saver.restore(sess, out_dir + '/check_points/final.ckpt')
    #     # fd = {data: crops, IS_TRAIN_PHASE: False}
    #     # test_prob = sess.run(prob, feed_dict=fd)

    test_prob = np.random.uniform(size=(num,num_class))


    # show results ------------------

    f=8
    results_image = 255. * np.ones(shape=(5*(f*height + 30), 6*f*width, channel), dtype=np.float32)

    for n in range(num):
        print('n=%d:' % n)
        crop = crops[n]
        #crop = cv2.resize(crop, (0, 0), fx=f, fy=f, interpolation=cv2.INTER_NN)
        crop = crop.repeat(f, axis=0).repeat(f, axis=1)
        insert_subimage(results_image, crop, n * (f*height + 30), 0)

        p = test_prob[n]
        idx = np.argsort(p)[::-1]
        for k in range(5):
            c = int(idx[k])
            label_image = get_label_image(c)
            #label_image = cv2.resize(label_image, (0, 0), fx=f, fy=f, interpolation=cv2.INTER_NN)
            label_image = label_image.repeat(f, axis=0).repeat(f, axis=1)
            insert_subimage(results_image, label_image, n * (f*height + 30), (k + 1) * f*width)


            print('\ttop%d: %f  %02d:%s' % (k, p[c], c, classnames[c]))
            cv2.putText(results_image, 'top%d: %f' % (k, p[c]), (5+(k + 1) * f*width, (n+1) * (f*height + 30)-27), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            cv2.putText(results_image, '%02d:%s%s' % (c, classnames[c][0:20], '...' if len(classnames[c])>20 else ''), (5+(k + 1) * f*width, (n+1) * (f*height + 30)-7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    imshow('results_image', results_image)
    cv2.waitKey(0)

## MAIN ##############################################################

if __name__ == '__main__':
    print('%s: calling main function ... ' % os.path.basename(__file__))
    run_train()
    #run_test()

    #run_extra_test()
